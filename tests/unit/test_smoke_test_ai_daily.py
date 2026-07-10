import unittest
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from services.ai_daily_source import DailyIssueCandidate
from services.rss_service import RssEntry


class AiDailySmokeTestTest(unittest.TestCase):
    def test_explicit_article_runs_read_only_parse_without_discovery(self):
        runtime = SimpleNamespace(
            discovery=Mock(),
            article_service=Mock(),
        )
        runtime.article_service.fetch.return_value = RssEntry(
            title="2026-07-10",
            link="https://mp.weixin.qq.com/s/article-id",
            published="2026-07-10T09:00:00+08:00",
            summary="AI 早报",
            content_html="<h2>新闻标题 <code>#1</code></h2><p>正文</p>",
            content_text="新闻标题 正文",
            entry_id="article-id",
        )

        from scripts.smoke_test_ai_daily import main

        with patch("scripts.smoke_test_ai_daily.build_ai_daily_runtime", return_value=runtime):
            exit_code = main(
                [
                    "--date",
                    "2026-07-10",
                    "--article-url",
                    "https://mp.weixin.qq.com/s/article-id",
                    "--video-url",
                    "https://www.bilibili.com/video/BV1test/",
                ]
            )

        self.assertEqual(exit_code, 0)
        runtime.discovery.discover_latest.assert_not_called()
        candidate = runtime.article_service.fetch.call_args.args[0]
        self.assertIsInstance(candidate, DailyIssueCandidate)
        self.assertEqual(candidate.issue_date, date(2026, 7, 10))
        self.assertEqual(candidate.published_at, datetime(2026, 7, 10, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
        self.assertEqual(candidate.video_url, "https://www.bilibili.com/video/BV1test/")


if __name__ == "__main__":
    unittest.main()
