import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.ai_daily_factory import build_ai_daily_runtime


class AiDailyFactoryTest(unittest.TestCase):
    def test_builds_bilibili_runtime_without_private_credentials(self):
        fake_config = SimpleNamespace(
            AI_DAILY_SOURCE_ORDER=["bilibili"],
            BILIBILI_UPLOADER_MID=285286947,
            BILIBILI_UPLOADER_NAME="橘鸦Juya",
            BILIBILI_SEARCH_KEYWORD="橘鸦Juya",
            WECHAT_ACCOUNT_NICKNAME="橘鸦Juya",
            WECHAT_API_BASE_URL="https://wxcrawl.touchturing.com",
            WECHAT_API_KEY="",
            WECHAT_API_SECRET="",
        )

        with patch("services.ai_daily_factory.config", fake_config):
            runtime = build_ai_daily_runtime()

        self.assertEqual([type(source).__name__ for source in runtime.discovery.sources], ["BilibiliDailySource"])
        self.assertEqual(runtime.article_service.account_nickname, "橘鸦Juya")

    def test_private_source_precedes_bilibili_with_credentials(self):
        fake_config = SimpleNamespace(
            AI_DAILY_SOURCE_ORDER=["wechat_private", "bilibili"],
            BILIBILI_UPLOADER_MID=285286947,
            BILIBILI_UPLOADER_NAME="橘鸦Juya",
            BILIBILI_SEARCH_KEYWORD="橘鸦Juya",
            WECHAT_ACCOUNT_NICKNAME="橘鸦Juya",
            WECHAT_API_BASE_URL="https://private.example",
            WECHAT_API_KEY="fake-key",
            WECHAT_API_SECRET="fake-secret",
        )

        with patch("services.ai_daily_factory.config", fake_config):
            runtime = build_ai_daily_runtime()

        self.assertEqual(
            [type(source).__name__ for source in runtime.discovery.sources],
            ["WechatPrivateDailySource", "BilibiliDailySource"],
        )
        self.assertIsNotNone(runtime.article_service.markdown_extractor)


if __name__ == "__main__":
    unittest.main()
