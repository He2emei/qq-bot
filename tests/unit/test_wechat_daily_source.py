import unittest
from datetime import date
from unittest.mock import Mock

from services.ai_daily_source import DailySourceError
from services.wechat_daily_source import WechatPrivateDailySource


class WechatPrivateDailySourceTest(unittest.TestCase):
    def test_converts_latest_valid_article_to_candidate(self):
        client = Mock()
        client.get_latest_articles.return_value = {
            "data": [
                {
                    "title": "今日标题【AI 早报 2026-07-10】",
                    "link": "https://mp.weixin.qq.com/s/article-id",
                    "create_time": 1783645200,
                    "nickname": "橘鸦Juya",
                }
            ]
        }

        result = WechatPrivateDailySource(client, "橘鸦Juya").discover_latest()

        self.assertEqual(result.issue_date, date(2026, 7, 10))
        self.assertEqual(result.article_url, "https://mp.weixin.qq.com/s/article-id")
        self.assertEqual(result.discovered_by, "wechat_private")

    def test_rejects_malformed_data_and_wrong_nickname(self):
        client = Mock()
        client.get_latest_articles.return_value = {"data": "bad"}

        with self.assertRaises(DailySourceError):
            WechatPrivateDailySource(client, "橘鸦Juya").discover_latest()

        client.get_latest_articles.return_value = {
            "data": [
                {
                    "title": "标题【AI 早报 2026-07-10】",
                    "link": "https://mp.weixin.qq.com/s/x",
                    "create_time": 1783645200,
                    "nickname": "其他账号",
                }
            ]
        }

        with self.assertRaises(DailySourceError):
            WechatPrivateDailySource(client, "橘鸦Juya").discover_latest()


if __name__ == "__main__":
    unittest.main()
