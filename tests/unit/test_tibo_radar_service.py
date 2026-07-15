import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from services.tibo_radar_service import (
    TiboPost,
    TiboRadar,
    TiboRadarStateStore,
    TwitterApiIoSource,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self.payload


def post(post_id, minute=0, text=None, is_reply=False):
    return TiboPost(
        post_id=str(post_id),
        text=text or f"post {post_id}",
        created_at=datetime(2026, 7, 16, 1, minute, tzinfo=timezone.utc),
        url=f"https://x.com/thsottiaux/status/{post_id}",
        is_reply=is_reply,
    )


class TwitterApiIoSourceTest(unittest.TestCase):
    def test_fetch_since_normalizes_authored_posts_and_excludes_native_retweets(self):
        session = Mock()
        session.get.return_value = FakeResponse(
            {
                "tweets": [
                    {
                        "id": "200",
                        "text": "A reply",
                        "createdAt": "2026-07-16T01:02:00Z",
                        "url": "https://x.com/thsottiaux/status/200",
                        "isReply": True,
                    }
                ]
            }
        )
        source = TwitterApiIoSource("secret", "thsottiaux", session=session)

        result = source.fetch_since(
            datetime(2026, 7, 16, 1, 0, tzinfo=timezone.utc),
            datetime(2026, 7, 16, 1, 5, tzinfo=timezone.utc),
        )

        self.assertEqual([item.post_id for item in result], ["200"])
        self.assertTrue(result[0].is_reply)
        _, kwargs = session.get.call_args
        self.assertIn("from:thsottiaux", kwargs["params"]["query"])
        self.assertIn("-filter:nativeretweets", kwargs["params"]["query"])
        self.assertNotIn("secret", str(kwargs["params"]))

    def test_fetch_since_follows_all_result_pages(self):
        session = Mock()
        session.get.side_effect = [
            FakeResponse(
                {
                    "tweets": [{"id": "201", "text": "one", "createdAt": "2026-07-16T01:01:00Z"}],
                    "has_next_page": True,
                    "next_cursor": "next-page",
                }
            ),
            FakeResponse(
                {
                    "tweets": [{"id": "202", "text": "two", "createdAt": "2026-07-16T01:02:00Z"}],
                    "has_next_page": False,
                }
            ),
        ]
        source = TwitterApiIoSource("secret", "thsottiaux", session=session)

        result = source.fetch_since(
            datetime(2026, 7, 16, 1, 0, tzinfo=timezone.utc),
            datetime(2026, 7, 16, 1, 5, tzinfo=timezone.utc),
        )

        self.assertEqual([item.post_id for item in result], ["201", "202"])
        self.assertEqual(session.get.call_args_list[1].kwargs["params"]["cursor"], "next-page")

    def test_fetch_since_fails_instead_of_advancing_after_page_safety_limit(self):
        session = Mock()
        session.get.return_value = FakeResponse(
            {"tweets": [], "has_next_page": True, "next_cursor": "same-cursor"}
        )
        source = TwitterApiIoSource("secret", "thsottiaux", session=session)

        with self.assertRaisesRegex(Exception, "分页游标"):
            source.fetch_since(
                datetime(2026, 7, 16, 1, 0, tzinfo=timezone.utc),
                datetime(2026, 7, 16, 1, 5, tzinfo=timezone.utc),
            )


class TiboRadarTest(unittest.TestCase):
    def make_radar(self, directory, source, sender, bootstrap_send=False):
        store = TiboRadarStateStore(str(Path(directory) / "state.json"))
        return TiboRadar(
            source=source,
            state_store=store,
            sender=sender,
            group_id=1105591264,
            bootstrap_send=bootstrap_send,
        ), store

    def test_first_check_seeds_state_without_flooding_old_posts(self):
        with TemporaryDirectory() as directory:
            source = Mock()
            source.fetch_since.return_value = [post(100), post(101, 1)]
            sender = Mock(return_value={"status": "ok"})
            radar, store = self.make_radar(directory, source, sender)

            result = radar.check_and_push(datetime(2026, 7, 16, 2, tzinfo=timezone.utc))

            self.assertEqual(result.seeded_ids, ["100", "101"])
            sender.assert_not_called()
            self.assertTrue(store.is_completed("100", 1105591264))
            self.assertTrue(store.is_completed("101", 1105591264))

    def test_new_posts_are_sent_oldest_first_and_only_to_configured_group(self):
        with TemporaryDirectory() as directory:
            source = Mock()
            source.fetch_since.side_effect = [[post(100)], [post(102, 2), post(101, 1, is_reply=True)]]
            sender = Mock(return_value={"status": "ok"})
            radar, _ = self.make_radar(directory, source, sender)
            radar.check_and_push(datetime(2026, 7, 16, 2, tzinfo=timezone.utc))

            result = radar.check_and_push(datetime(2026, 7, 16, 2, 5, tzinfo=timezone.utc))

            self.assertEqual(result.pushed_ids, ["101", "102"])
            self.assertEqual([call.args[0] for call in sender.call_args_list], [1105591264, 1105591264])
            self.assertIn("回复", sender.call_args_list[0].args[1])

    def test_failed_delivery_is_not_marked_and_is_retried(self):
        with TemporaryDirectory() as directory:
            source = Mock()
            source.fetch_since.side_effect = [[post(100)], [post(101)], [post(101)]]
            sender = Mock(side_effect=[None, {"status": "ok"}])
            radar, store = self.make_radar(directory, source, sender)
            radar.check_and_push(datetime(2026, 7, 16, 2, tzinfo=timezone.utc))

            first = radar.check_and_push(datetime(2026, 7, 16, 2, 5, tzinfo=timezone.utc))
            second = radar.check_and_push(datetime(2026, 7, 16, 2, 10, tzinfo=timezone.utc))

            self.assertEqual(first.failed_ids, ["101"])
            self.assertEqual(second.pushed_ids, ["101"])
            self.assertTrue(store.is_completed("101", 1105591264))

    def test_stream_delivery_does_not_advance_search_backfill_watermark(self):
        with TemporaryDirectory() as directory:
            source = Mock()
            source.fetch_since.return_value = [post(100)]
            radar, store = self.make_radar(directory, source, Mock(return_value={"status": "ok"}))
            initial_check = datetime(2026, 7, 16, 2, tzinfo=timezone.utc)
            radar.check_and_push(initial_check)

            radar.push_posts([post(101, 1)], datetime(2026, 7, 16, 3, tzinfo=timezone.utc))

            self.assertEqual(
                store.query_since(datetime(2026, 7, 16, 4, tzinfo=timezone.utc)),
                datetime(2026, 7, 16, 1, 55, tzinfo=timezone.utc),
            )

    def test_failed_stream_delivery_is_persisted_and_retried_without_source(self):
        with TemporaryDirectory() as directory:
            source = Mock()
            source.fetch_since.return_value = []
            sender = Mock(side_effect=[False, True])
            radar, store = self.make_radar(directory, source, sender)
            now = datetime(2026, 7, 16, 3, tzinfo=timezone.utc)

            first = radar.push_posts([post(101, 1)], now)
            second = radar.check_and_push(now + timedelta(minutes=1))

            self.assertEqual(first.failed_ids, ["101"])
            self.assertEqual(second.pushed_ids, ["101"])
            source.fetch_since.assert_called_once()
            self.assertEqual(store.load().get("pending"), {})
            self.assertTrue(store.is_completed("101", 1105591264))

    def test_failed_pending_delivery_prevents_source_call_until_retry_succeeds(self):
        with TemporaryDirectory() as directory:
            source = Mock()
            radar, store = self.make_radar(directory, source, Mock(return_value=False))
            now = datetime(2026, 7, 16, 3, tzinfo=timezone.utc)
            radar.push_posts([post(101, 1)], now)

            result = radar.check_and_push(now + timedelta(minutes=1))

            self.assertEqual(result.failed_ids, ["101"])
            source.fetch_since.assert_not_called()
            self.assertEqual(store.load()["pending"]["101"]["received_at"], now.isoformat())


if __name__ == "__main__":
    unittest.main()
