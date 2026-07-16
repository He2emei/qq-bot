import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from services.apify_tibo_source import ApifyTiboSource, MAXIMEDUPRE_ACTOR_ID
from services.tibo_radar_service import TiboSourceError, format_tibo_post


class FakeResponse:
    def __init__(self, payload, headers=None):
        self.payload = payload
        self.headers = headers or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class ApifyTiboSourceTest(unittest.TestCase):
    def make_source(self, payload):
        session = Mock()
        session.post.return_value = FakeResponse(payload)
        source = ApifyTiboSource(
            "apify-secret",
            "thsottiaux",
            session=session,
            max_items=25,
        )
        return source, session

    def test_fetch_since_normalizes_target_posts_and_requests_bounded_timeline(self):
        source, session = self.make_source(
            [
                {
                    "tweetId": "401",
                    "text": "new post",
                    "createdAt": "2026-07-16T03:00:00Z",
                    "author": {"userName": "thsottiaux"},
                    "url": "https://x.com/thsottiaux/status/401",
                },
                {
                    "id": "402",
                    "text": "reply",
                    "createdAt": "2026-07-16T03:01:00Z",
                    "author": {"username": "thsottiaux"},
                    "inReplyToId": "400",
                },
                {
                    "id": "403",
                    "text": "wrong author",
                    "createdAt": "2026-07-16T03:02:00Z",
                    "author": {"userName": "someone_else"},
                },
            ]
        )

        posts = source.fetch_since(
            datetime(2026, 7, 16, 2, tzinfo=timezone.utc),
            datetime(2026, 7, 16, 4, tzinfo=timezone.utc),
        )

        self.assertEqual([post.post_id for post in posts], ["401", "402"])
        self.assertTrue(posts[1].is_reply)
        self.assertIn("信源: Apify Store Actor", format_tibo_post(posts[0]))
        request = session.post.call_args
        self.assertEqual(
            request.kwargs["json"]["query"],
            "from:thsottiaux -filter:retweets",
        )
        self.assertEqual(request.kwargs["json"]["queryType"], "Latest")
        self.assertEqual(request.kwargs["json"]["maxItems"], 25)
        self.assertEqual(
            request.kwargs["headers"]["Authorization"], "Bearer apify-secret"
        )
        self.assertNotIn("token", request.kwargs["params"])
        self.assertIn("seemuapps~x-tweet-scraper", request.args[0])

    def test_fetch_since_excludes_native_retweets_and_old_items(self):
        source, _ = self.make_source(
            [
                {
                    "id": "404",
                    "text": "RT @someone old",
                    "createdAt": "2026-07-16T03:00:00Z",
                    "isRetweet": True,
                },
                {
                    "id": "405",
                    "text": "too old",
                    "createdAt": "2026-07-15T03:00:00Z",
                },
                {
                    "id": "406",
                    "text": "RT @someone: unflagged native retweet",
                    "createdAt": "2026-07-16T03:01:00Z",
                },
            ]
        )

        posts = source.fetch_since(
            datetime(2026, 7, 16, 2, tzinfo=timezone.utc),
            datetime(2026, 7, 16, 4, tzinfo=timezone.utc),
        )

        self.assertEqual(posts, [])

    def test_free_actor_caps_max_items_at_25(self):
        source = ApifyTiboSource("secret", "thsottiaux", max_items=100)

        self.assertEqual(source.max_items, 25)

    def test_fetch_since_fails_on_actor_error_only_response(self):
        source, _ = self.make_source([{"errorCode": "RATE_LIMITED"}])

        with self.assertRaisesRegex(TiboSourceError, "错误记录"):
            source.fetch_since(
                datetime(2026, 7, 16, 2, tzinfo=timezone.utc),
                datetime(2026, 7, 16, 4, tzinfo=timezone.utc),
            )

    def test_fetch_since_fails_when_actor_records_have_unknown_schema(self):
        source, _ = self.make_source([{}])

        with self.assertRaisesRegex(TiboSourceError, "字段无法识别"):
            source.fetch_since(
                datetime(2026, 7, 16, 2, tzinfo=timezone.utc),
                datetime(2026, 7, 16, 4, tzinfo=timezone.utc),
            )

    def test_maximedupre_fetch_uses_incremental_id_and_normalizes_posts(self):
        session = Mock()
        session.post.return_value = FakeResponse(
            [
                {
                    "postId": "2077632589498913088",
                    "postText": "A reply",
                    "postDateTime": "2026-07-16T03:01:00.000Z",
                    "postUrl": "https://x.com/thsottiaux/status/2077632589498913088",
                    "authorHandle": "thsottiaux",
                    "replyToPostId": "2077632589498913000",
                }
            ]
        )
        source = ApifyTiboSource(
            "secret",
            "thsottiaux",
            actor_id=MAXIMEDUPRE_ACTOR_ID,
            max_items=4,
            session=session,
        )

        posts = source.fetch_since_id(
            "2077632589498913087",
            datetime(2026, 7, 16, 3, tzinfo=timezone.utc),
            datetime(2026, 7, 16, 4, tzinfo=timezone.utc),
        )

        self.assertEqual([post.post_id for post in posts], ["2077632589498913088"])
        self.assertTrue(posts[0].is_reply)
        actor_input = session.post.call_args.kwargs["json"]
        self.assertEqual(actor_input["fromUsers"], ["thsottiaux"])
        self.assertEqual(actor_input["sinceId"], "2077632589498913087")
        self.assertEqual(actor_input["maxNbItemsToScrape"], 4)
        self.assertFalse(actor_input["shouldIncludeReposts"])

    def test_maximedupre_empty_incremental_result_is_valid(self):
        session = Mock()
        session.post.return_value = FakeResponse([])
        source = ApifyTiboSource(
            "secret",
            "thsottiaux",
            actor_id=MAXIMEDUPRE_ACTOR_ID,
            session=session,
        )

        posts = source.fetch_since_id(
            "2077632589498913087",
            datetime(2026, 7, 16, 3, tzinfo=timezone.utc),
            datetime(2026, 7, 16, 4, tzinfo=timezone.utc),
        )

        self.assertEqual(posts, [])

    def test_maximedupre_records_actual_actor_run_cost_when_header_is_available(self):
        session = Mock()
        session.post.return_value = FakeResponse(
            [], headers={"X-Apify-Actor-Run-Id": "run-123"}
        )
        session.get.return_value = FakeResponse(
            {
                "data": {
                    "status": "SUCCEEDED",
                    "usageTotalUsd": 0,
                    "chargedEventCounts": {},
                }
            }
        )
        source = ApifyTiboSource(
            "secret",
            "thsottiaux",
            actor_id=MAXIMEDUPRE_ACTOR_ID,
            session=session,
        )

        source.fetch_since_id(
            "2077632589498913087",
            datetime(2026, 7, 16, 3, tzinfo=timezone.utc),
            datetime(2026, 7, 16, 4, tzinfo=timezone.utc),
        )

        self.assertEqual(source.last_run_metadata["run_id"], "run-123")
        self.assertEqual(source.last_run_metadata["usage_total_usd"], 0)
        self.assertEqual(source.last_run_metadata["status"], "SUCCEEDED")

    def test_maximedupre_reads_latest_run_cost_when_sync_header_is_missing(self):
        session = Mock()
        session.post.return_value = FakeResponse([])
        session.get.return_value = FakeResponse(
            {
                "data": {
                    "items": [
                        {
                            "id": "run-latest",
                            "status": "SUCCEEDED",
                            "usageTotalUsd": 0,
                            "chargedEventCounts": {},
                        }
                    ]
                }
            }
        )
        source = ApifyTiboSource(
            "secret",
            "thsottiaux",
            actor_id=MAXIMEDUPRE_ACTOR_ID,
            session=session,
        )

        source.fetch_since_id(
            "2077632589498913087",
            datetime(2026, 7, 16, 3, tzinfo=timezone.utc),
            datetime(2026, 7, 16, 4, tzinfo=timezone.utc),
        )

        self.assertEqual(source.last_run_metadata["run_id"], "run-latest")
        self.assertEqual(source.last_run_metadata["usage_total_usd"], 0)
        self.assertEqual(session.get.call_args.kwargs["params"], {"limit": 1, "desc": 1})


if __name__ == "__main__":
    unittest.main()
