import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from services.tibo_radar_factory import build_tibo_radar


def settings(api_key=""):
    return SimpleNamespace(
        TIBO_RADAR_API_KEY=api_key,
        TIBO_RADAR_API_BASE_URL="https://api.twitterapi.io",
        TIBO_RADAR_HANDLE="thsottiaux",
        TIBO_RADAR_GROUP_ID=1105591264,
        TIBO_RADAR_STATE_PATH="data/tibo_radar_state.json",
        TIBO_RADAR_BOOTSTRAP_SEND=False,
    )


class TiboRadarFactoryTest(unittest.TestCase):
    def test_missing_api_key_disables_radar_without_starting_network_work(self):
        self.assertIsNone(build_tibo_radar(settings(), sender=Mock()))

    def test_configured_radar_targets_only_ai_xjtu_group(self):
        radar = build_tibo_radar(settings("secret"), sender=Mock())

        self.assertEqual(radar.group_id, 1105591264)
        self.assertEqual(radar.source.handle, "thsottiaux")


if __name__ == "__main__":
    unittest.main()
