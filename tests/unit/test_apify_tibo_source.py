import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from services.apify_tibo_source import ApifyTiboSource
from services.tibo_radar_service import TiboSourceError, format_tibo_post


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

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
            max_items=4,
        )
        return source, session

    def test_fetch_since_normalizes_target_posts_and_requests_bounded_timeline(self):
        source, session = self.make_source(
            [
                {
                    "id": "401",
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
        self.assertEqual(request.kwargs["json"]["twitterHandles"], ["thsottiaux"])
        self.assertEqual(request.kwargs["json"]["maxItems"], 4)
        self.assertTrue(request.kwargs["json"]["includeReplies"])
        self.assertEqual(
            request.kwargs["headers"]["Authorization"], "Bearer apify-secret"
        )
        self.assertNotIn("token", request.kwargs["params"])

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
            ]
        )

        posts = source.fetch_since(
            datetime(2026, 7, 16, 2, tzinfo=timezone.utc),
            datetime(2026, 7, 16, 4, tzinfo=timezone.utc),
        )

        self.assertEqual(posts, [])

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


if __name__ == "__main__":
    unittest.main()
