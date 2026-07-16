import unittest
from types import SimpleNamespace

from services.tibo_radar_scheduler import _poll_interval_seconds


class TiboRadarSchedulerTest(unittest.TestCase):
    def test_apify_uses_free_tier_interval(self):
        settings = SimpleNamespace(
            TIBO_RADAR_PROVIDER="apify",
            TIBO_RADAR_POLL_INTERVAL_SECONDS=900,
            TIBO_RADAR_APIFY_POLL_INTERVAL_SECONDS=28800,
        )
        self.assertEqual(_poll_interval_seconds(settings), 28800)

    def test_twitterapi_keeps_regular_interval(self):
        settings = SimpleNamespace(
            TIBO_RADAR_PROVIDER="twitterapi",
            TIBO_RADAR_POLL_INTERVAL_SECONDS=900,
            TIBO_RADAR_APIFY_POLL_INTERVAL_SECONDS=28800,
        )
        self.assertEqual(_poll_interval_seconds(settings), 900)

    def test_apify_interval_cannot_exceed_three_runs_per_day(self):
        settings = SimpleNamespace(
            TIBO_RADAR_PROVIDER="apify",
            TIBO_RADAR_POLL_INTERVAL_SECONDS=900,
            TIBO_RADAR_APIFY_POLL_INTERVAL_SECONDS=60,
        )
        self.assertEqual(_poll_interval_seconds(settings), 28800)


if __name__ == "__main__":
    unittest.main()
