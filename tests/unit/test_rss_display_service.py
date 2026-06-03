import unittest

from services.rss_display_service import build_other_news_forward_nodes, format_important_news_message
from services.rss_filter_service import RssFilterResult, RssNewsItem
from services.rss_service import RssEntry


class RssDisplayServiceTest(unittest.TestCase):
    def test_format_important_news_message(self):
        result = _sample_filter_result()

        message = format_important_news_message(result)

        self.assertIn("今天是2026年06月03日，星期三，为您带来今日AI早报：", message)
        self.assertIn("1. 要闻标题", message)
        self.assertIn("3. 关键词重点标题", message)
        self.assertNotIn("2. 模型发布标题", message)

    def test_build_other_news_forward_nodes_groups_categories_with_headlines(self):
        result = _sample_filter_result()

        nodes = build_other_news_forward_nodes(result, bot_user_id=1919447403, bot_nickname="AI早报")

        self.assertEqual(len(nodes), 4)
        self.assertEqual(nodes[0]["type"], "node")
        source_text = nodes[0]["data"]["content"][0]["data"]["text"]
        self.assertIn("原文链接：https://example.com/issue", source_text)
        self.assertIn("哔哩哔哩视频版：https://www.bilibili.com/video/BV123", source_text)

        headline_text = nodes[1]["data"]["content"][0]["data"]["text"]
        self.assertIn("【要闻】", headline_text)
        self.assertIn("#1 要闻标题", headline_text)
        self.assertIn("https://example.com/1", headline_text)

        model_text = nodes[2]["data"]["content"][0]["data"]["text"]
        self.assertIn("【模型发布】", model_text)
        self.assertIn("#2 模型发布标题", model_text)

        dev_text = nodes[3]["data"]["content"][0]["data"]["text"]
        self.assertIn("【开发生态】", dev_text)
        self.assertIn("#3 关键词重点标题", dev_text)


def _sample_filter_result():
    entry = RssEntry(
        title="2026-06-03",
        link="https://example.com/issue",
        published="Wed, 03 Jun 2026 00:00:00 +0000",
        summary="summary",
        content_html='<p>视频版：<a href="https://www.bilibili.com/video/BV123">哔哩哔哩</a></p>',
        content_text="",
        entry_id="entry-id",
    )
    headline = RssNewsItem(
        number=1,
        title="要闻标题",
        url="https://example.com/1",
        category="要闻",
        content_text="",
        source_important=True,
        matched_keywords=[],
    )
    model = RssNewsItem(
        number=2,
        title="模型发布标题",
        url="https://example.com/2",
        category="模型发布",
        content_text="",
        source_important=False,
        matched_keywords=[],
    )
    keyword = RssNewsItem(
        number=3,
        title="关键词重点标题",
        url="https://example.com/3",
        category="开发生态",
        content_text="",
        source_important=False,
        matched_keywords=["Codex"],
    )
    return RssFilterResult(
        entry=entry,
        keywords=["Codex"],
        all_items=[headline, model, keyword],
        important_items=[headline, keyword],
        other_items=[model],
    )


if __name__ == "__main__":
    unittest.main()
