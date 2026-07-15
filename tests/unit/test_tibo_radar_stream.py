import unittest
from unittest.mock import Mock

from services.tibo_radar_stream import TwitterApiIoRuleClient, posts_from_stream_event


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class TwitterApiIoRuleClientTest(unittest.TestCase):
    def test_existing_matching_rule_is_reused(self):
        session = Mock()
        session.get.return_value = FakeResponse(
            {"rules": [{"rule_id": "r1", "tag": "qq-bot-tibo", "value": "from:thsottiaux -filter:nativeretweets"}]}
        )
        client = TwitterApiIoRuleClient("secret", session=session)

        rule_id = client.ensure_rule("qq-bot-tibo", "from:thsottiaux -filter:nativeretweets", 5)

        self.assertEqual(rule_id, "r1")
        session.post.assert_not_called()

    def test_missing_rule_is_registered(self):
        session = Mock()
        session.get.return_value = FakeResponse({"rules": []})
        session.post.return_value = FakeResponse({"rule_id": "new-rule"})
        client = TwitterApiIoRuleClient("secret", session=session)

        rule_id = client.ensure_rule("qq-bot-tibo", "from:thsottiaux -filter:nativeretweets", 5)

        self.assertEqual(rule_id, "new-rule")
        self.assertEqual(session.post.call_args.kwargs["data"]["interval_seconds"], 5)

    def test_rule_event_normalizes_only_target_author(self):
        posts = posts_from_stream_event(
            {
                "event_type": "tweet",
                "tweets": [
                    {
                        "id": "301",
                        "text": "hello",
                        "createdAt": "2026-07-16T03:00:00Z",
                        "author": {"username": "thsottiaux"},
                    },
                    {
                        "id": "302",
                        "text": "wrong author",
                        "createdAt": "2026-07-16T03:00:01Z",
                        "author": {"username": "someone_else"},
                    },
                ],
            },
            "thsottiaux",
        )

        self.assertEqual([post.post_id for post in posts], ["301"])


if __name__ == "__main__":
    unittest.main()
