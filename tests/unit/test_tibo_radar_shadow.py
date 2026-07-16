import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from services.tibo_radar_service import TiboPost
from services.tibo_radar_shadow import run_shadow_check


def post(post_id, minute, text="private text"):
    return TiboPost(
        post_id=str(post_id),
        text=text,
        created_at=datetime(2026, 7, 16, 3, minute, tzinfo=timezone.utc),
        url=f"https://x.com/thsottiaux/status/{post_id}",
        is_reply=minute % 2 == 1,
        source_label="Apify Store Actor（非 X 官方 API）",
    )


class TiboRadarShadowTest(unittest.TestCase):
    def test_run_records_metadata_and_advances_incremental_cursor(self):
        with TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            log_path = Path(directory) / "observations.jsonl"
            source = Mock()
            source.fetch_since_id.return_value = [post(100, 1), post(101, 2)]
            now = datetime(2026, 7, 16, 4, tzinfo=timezone.utc)

            result = run_shadow_check(source, state_path, log_path, now=now)

            self.assertEqual(result["observed_ids"], ["100", "101"])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["latest_post_id"], "101")
            self.assertEqual(state["run_count"], 1)
            event = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(event["posts"][0]["post_id"], "100")
            self.assertNotIn("private text", log_path.read_text(encoding="utf-8"))
            source.fetch_since_id.assert_called_once_with(
                None,
                datetime(2026, 7, 15, 4, tzinfo=timezone.utc),
                now,
            )

    def test_empty_run_keeps_cursor_and_records_success(self):
        with TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            log_path = Path(directory) / "observations.jsonl"
            state_path.write_text(
                json.dumps(
                    {
                        "latest_post_id": "101",
                        "last_checked_at": "2026-07-16T03:55:00+00:00",
                        "run_count": 1,
                    }
                ),
                encoding="utf-8",
            )
            source = Mock()
            source.fetch_since_id.return_value = []
            now = datetime(2026, 7, 16, 4, tzinfo=timezone.utc)

            result = run_shadow_check(source, state_path, log_path, now=now)

            self.assertEqual(result["observed_ids"], [])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["latest_post_id"], "101")
            self.assertEqual(state["run_count"], 2)
            source.fetch_since_id.assert_called_once_with(
                "101",
                datetime(2026, 7, 16, 3, 50, tzinfo=timezone.utc),
                now,
            )


if __name__ == "__main__":
    unittest.main()
