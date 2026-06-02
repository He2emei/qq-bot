import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.rss_push_service as rss_push_service
from services.rss_push_service import RssPushStateStore, check_and_push_latest_rss
from services.rss_service import RssEntry


class RssPushServiceTest(unittest.TestCase):
    def test_state_store_marks_last_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RssPushStateStore(str(Path(temp_dir) / "rss_state.json"))
            entry = _sample_entry("entry-1")

            self.assertEqual(store.get_last_entry_id(), "")

            store.mark_pushed(entry)

            self.assertEqual(store.get_last_entry_id(), "entry-1")

    def test_check_and_push_latest_rss_skips_duplicate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RssPushStateStore(str(Path(temp_dir) / "rss_state.json"))
            entry = _sample_entry("entry-1")

            with patch.object(rss_push_service, "rss_push_state_store", store), \
                 patch.object(rss_push_service, "fetch_rss_entries", return_value=[entry]), \
                 patch.object(rss_push_service, "push_rss_entry") as push_mock:
                first_result = check_and_push_latest_rss()
                second_result = check_and_push_latest_rss()

            self.assertTrue(first_result.pushed)
            self.assertFalse(second_result.pushed)
            self.assertEqual(push_mock.call_count, 1)

    def test_check_and_push_latest_rss_force_sends_duplicate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RssPushStateStore(str(Path(temp_dir) / "rss_state.json"))
            entry = _sample_entry("entry-1")
            store.mark_pushed(entry)

            with patch.object(rss_push_service, "rss_push_state_store", store), \
                 patch.object(rss_push_service, "fetch_rss_entries", return_value=[entry]), \
                 patch.object(rss_push_service, "push_rss_entry") as push_mock:
                result = check_and_push_latest_rss(force=True)

            self.assertTrue(result.pushed)
            push_mock.assert_called_once()


def _sample_entry(entry_id: str):
    return RssEntry(
        title="2026-06-03",
        link="https://example.com/issue",
        published="Wed, 03 Jun 2026 00:00:00 +0000",
        summary="summary",
        content_html="<h1>content</h1>",
        content_text="content",
        entry_id=entry_id,
    )


if __name__ == "__main__":
    unittest.main()
