import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import ANY, Mock, patch

import services.rss_push_service as rss_push_service
from services.rss_push_service import (
    RssPushError,
    RssPushStateStore,
    check_and_push_latest_rss,
    push_rss_entry,
)
from services.rss_service import RssEntry


class RssPushServiceTest(unittest.TestCase):
    def test_legacy_state_migrates_without_resend(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rss_state.json"
            path.write_text('{"last_entry_id":"entry-1"}', encoding="utf-8")
            store = RssPushStateStore(str(path))

            completed = store.completed_groups("entry-1", [11, 22])

            self.assertEqual(completed, {11, 22})
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(data["groups"]), {"11", "22"})

    def test_corrupt_state_recovers_as_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rss_state.json"
            path.write_text("{broken", encoding="utf-8")
            store = RssPushStateStore(str(path))

            self.assertEqual(store.completed_groups("entry-1", [11]), set())

    def test_partial_failure_retries_only_failed_group(self):
        entry = _sample_entry("entry-1")
        runtime = Mock()
        runtime.discovery.discover_latest.return_value = Mock()
        runtime.article_service.fetch.return_value = entry

        with tempfile.TemporaryDirectory() as temp_dir:
            store = RssPushStateStore(str(Path(temp_dir) / "rss_state.json"))
            with patch.object(rss_push_service, "send_group_message", return_value={"ok": True}), patch.object(
                rss_push_service,
                "send_group_forward_message",
                side_effect=[{"ok": True}, None],
            ):
                first = check_and_push_latest_rss(group_ids=[11, 22], runtime=runtime, state_store=store)

            self.assertEqual(first.group_ids, [11])
            self.assertEqual(first.failed_group_ids, [22])

            with patch.object(rss_push_service, "send_group_message", return_value={"ok": True}) as plain, patch.object(
                rss_push_service,
                "send_group_forward_message",
                return_value={"ok": True},
            ):
                second = check_and_push_latest_rss(group_ids=[11, 22], runtime=runtime, state_store=store)

            plain.assert_called_once_with(22, ANY)
            self.assertEqual(second.group_ids, [22])
            self.assertEqual(second.failed_group_ids, [])

    def test_force_sends_completed_group_again(self):
        entry = _sample_entry("entry-1")
        runtime = Mock()
        runtime.discovery.discover_latest.return_value = Mock()
        runtime.article_service.fetch.return_value = entry

        with tempfile.TemporaryDirectory() as temp_dir:
            store = RssPushStateStore(str(Path(temp_dir) / "rss_state.json"))
            store.mark_group_pushed(entry, 11)
            with patch.object(rss_push_service, "send_group_message", return_value={"ok": True}) as plain, patch.object(
                rss_push_service,
                "send_group_forward_message",
                return_value={"ok": True},
            ):
                result = check_and_push_latest_rss(force=True, group_ids=[11], runtime=runtime, state_store=store)

            self.assertTrue(result.pushed)
            plain.assert_called_once_with(11, ANY)

    def test_zero_news_never_sends(self):
        entry = replace(_sample_entry("empty"), content_html="<h1>empty</h1>")

        with patch.object(rss_push_service, "send_group_message") as send:
            with self.assertRaisesRegex(RssPushError, "没有解析到新闻"):
                push_rss_entry(entry, [11], state_store=Mock())

        send.assert_not_called()


def _sample_entry(entry_id: str):
    return RssEntry(
        title="2026-06-03",
        link="https://example.com/issue",
        published="Wed, 03 Jun 2026 00:00:00 +0000",
        summary="summary",
        content_html="""<h3>要闻</h3><ul><li>测试新闻 #1</li></ul>
<h2>测试新闻 #1</h2><p>https://example.com/source</p>""",
        content_text="",
        entry_id=entry_id,
    )


if __name__ == "__main__":
    unittest.main()
