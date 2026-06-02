import tempfile
import unittest
from pathlib import Path

from services.rss_filter_service import RssKeywordStore, classify_rss_entry
from services.rss_service import RssEntry


class RssFilterServiceTest(unittest.TestCase):
    def test_classify_rss_entry_splits_source_important_and_keyword_matches(self):
        entry = RssEntry(
            title="2026-06-03",
            link="https://example.com/issue",
            published="Wed, 03 Jun 2026 00:00:00 +0000",
            summary="short summary",
            content_html="""<h1>AI Daily</h1>
<h2>概览</h2>
<h3>要闻</h3>
<ul>
  <li>Claude 发布新功能 <a href="https://example.com/claude">↗</a> <code>#1</code></li>
</ul>
<h3>模型发布</h3>
<ul>
  <li>普通模型更新 <a href="https://example.com/normal">↗</a> <code>#2</code></li>
  <li>Gemini 工具更新 <a href="https://example.com/gemini">↗</a> <code>#3</code></li>
</ul>
<hr />
<h2><a href="https://example.com/claude">Claude 发布新功能</a> <code>#1</code></h2>
<blockquote><p>来自信息源要闻。</p></blockquote>
<p>正文一。</p>
<hr />
<h2><a href="https://example.com/normal">普通模型更新</a> <code>#2</code></h2>
<p>正文二。</p>
<hr />
<h2><a href="https://example.com/gemini">Gemini 工具更新</a> <code>#3</code></h2>
<p>正文三。</p>""",
            content_text="",
            entry_id="test-entry",
        )

        result = classify_rss_entry(entry, keywords=["Gemini"])

        self.assertEqual([item.number for item in result.important_items], [1, 3])
        self.assertEqual([item.number for item in result.other_items], [2])
        self.assertTrue(result.important_items[0].source_important)
        self.assertEqual(result.important_items[1].matched_keywords, ["Gemini"])

    def test_keyword_store_add_delete_set_and_clear(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RssKeywordStore(str(Path(temp_dir) / "rss_keywords.json"))

            self.assertEqual(store.list_keywords(), ["Claude", "DeepSeek", "Codex", "Gemini", "Antigravity"])

            added = store.add_keywords(["Claude", "Qwen"])
            self.assertEqual(added, ["Qwen"])
            self.assertIn("Qwen", store.list_keywords())

            deleted = store.delete_keywords(["claude", "missing"])
            self.assertEqual(deleted, ["Claude"])
            self.assertNotIn("Claude", store.list_keywords())

            replaced = store.replace_keyword("qwen", "Gemini")
            self.assertTrue(replaced)
            self.assertNotIn("Qwen", store.list_keywords())
            self.assertEqual(store.list_keywords().count("Gemini"), 1)

            updated = store.set_keywords(["Gemini", "gemini", "Codex"])
            self.assertEqual(updated, ["Gemini", "Codex"])

            store.clear_keywords()
            self.assertEqual(store.list_keywords(), [])


if __name__ == "__main__":
    unittest.main()
