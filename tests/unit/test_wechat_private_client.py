import hashlib
import unittest
from unittest.mock import Mock

from services.wechat_private_client import WechatPrivateApiClient


class WechatPrivateApiClientTest(unittest.TestCase):
    def test_signing_matches_reference_for_empty_and_nonempty_body(self):
        client = WechatPrivateApiClient("key", "secret", clock=lambda: 1000)

        empty_headers = client._get_headers("/api/latest_articles")
        body = b'{"names":["account"]}'
        body_headers = client._get_headers("/api/example", body=body)

        self.assertEqual(
            empty_headers["x-signature"],
            hashlib.md5(b"key/api/latest_articles1000secret").hexdigest(),
        )
        body_md5 = hashlib.md5(body).hexdigest()
        self.assertEqual(
            body_headers["x-signature"],
            hashlib.md5(f"key/api/example1000{body_md5}secret".encode()).hexdigest(),
        )
        self.assertEqual(empty_headers["x-timestamp"], "1000")

    def test_latest_articles_uses_signed_get(self):
        session = Mock()
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"data": []}
        session.get.return_value = response
        client = WechatPrivateApiClient("key", "secret", session=session, clock=lambda: 1000)

        payload = client.get_latest_articles("橘鸦Juya", count=5)

        self.assertEqual(payload, {"data": []})
        session.get.assert_called_once_with(
            "https://wxcrawl.touchturing.com/api/latest_articles",
            headers=unittest.mock.ANY,
            params={"nickname": "橘鸦Juya", "count": 5, "offset": 0},
            timeout=(5, 20),
        )

    def test_extract_markdown_unquotes_json_string_response(self):
        session = Mock()
        response = Mock(text='"# AI 早报"')
        response.raise_for_status.return_value = None
        response.json.return_value = "# AI 早报"
        session.get.return_value = response
        client = WechatPrivateApiClient("key", "secret", session=session, clock=lambda: 1000)

        self.assertEqual(client.extract_markdown("https://mp.weixin.qq.com/s/article-id"), "# AI 早报")


if __name__ == "__main__":
    unittest.main()
