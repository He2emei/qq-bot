import unittest
from datetime import date, datetime
from unittest.mock import Mock

from services.ai_daily_source import DailyIssueCandidate
from services.wechat_article_service import WechatArticleError, WechatArticleService


HTML = """<html><body>
<h1 id="activity-name">今日【AI 早报 2026-07-10】</h1>
<span id="js_name">橘鸦Juya</span>
<div id="js_content"><h3>要闻</h3><ul><li>新闻 #1</li></ul>
<h2>新闻标题 #1</h2><p>正文 https://example.com/source</p></div>
</body></html>"""


def candidate(url="https://mp.weixin.qq.com/s/article-id"):
    return DailyIssueCandidate(
        title="今日【AI 早报 2026-07-10】",
        article_url=url,
        published_at=datetime.fromisoformat("2026-07-10T09:00:00+08:00"),
        issue_date=date(2026, 7, 10),
        source_id="source",
        video_url="https://www.bilibili.com/video/BV1/",
        discovered_by="bilibili",
    )


class WechatArticleServiceTest(unittest.TestCase):
    def make_service(self, html=HTML, final_url="https://mp.weixin.qq.com/s/article-id?nwr_flag=1"):
        response = Mock(status_code=200, text=html, url=final_url)
        response.raise_for_status.return_value = None
        session = Mock()
        session.get.return_value = response
        return WechatArticleService("橘鸦Juya", session=session), session

    def test_fetches_valid_article_as_rss_entry(self):
        service, _ = self.make_service()

        entry = service.fetch(candidate())

        self.assertEqual(entry.title, "2026-07-10")
        self.assertEqual(entry.link, "https://mp.weixin.qq.com/s/article-id")
        self.assertEqual(entry.entry_id, entry.link)
        self.assertEqual(entry.video_url, "https://www.bilibili.com/video/BV1/")
        self.assertEqual(entry.discovery_source, "bilibili")
        self.assertIn("新闻标题", entry.content_text)

    def test_rejects_non_wechat_url_without_network(self):
        service, session = self.make_service()

        with self.assertRaisesRegex(WechatArticleError, "微信文章域名"):
            service.fetch(candidate("https://example.com/article"))

        session.get.assert_not_called()

    def test_rejects_wrong_account(self):
        service, _ = self.make_service(HTML.replace("橘鸦Juya", "其他账号"))

        with self.assertRaisesRegex(WechatArticleError, "公众号不匹配"):
            service.fetch(candidate())

    def test_rejects_wrong_date_or_missing_content(self):
        service, _ = self.make_service(HTML.replace("2026-07-10", "2026-07-09"))

        with self.assertRaisesRegex(WechatArticleError, "日期不匹配"):
            service.fetch(candidate())

        service, _ = self.make_service(HTML.replace('id="js_content"', 'id="missing"'))
        with self.assertRaisesRegex(WechatArticleError, "正文"):
            service.fetch(candidate())


if __name__ == "__main__":
    unittest.main()
