import unittest
from unittest.mock import patch

from handlers.rss_handler import handle_rss_daily_command


class RssHandlerTest(unittest.TestCase):
    @patch("handlers.rss_handler.check_and_push_latest_rss")
    def test_manual_command_uses_force_pipeline(self, check):
        handle_rss_daily_command({"group_id": 123, "message": "#rssdaily"})

        check.assert_called_once_with(force=True, group_ids=[123])


if __name__ == "__main__":
    unittest.main()
