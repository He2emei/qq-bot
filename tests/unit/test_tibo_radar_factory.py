import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from services.tibo_radar_factory import build_tibo_radar


def settings(api_key="", provider="twitterapi", apify_token=""):
    return SimpleNamespace(
        TIBO_RADAR_PROVIDER=provider,
        TIBO_RADAR_API_KEY=api_key,
        TIBO_RADAR_API_BASE_URL="https://api.twitterapi.io",
        TIBO_RADAR_HANDLE="thsottiaux",
        TIBO_RADAR_GROUP_ID=1105591264,
        TIBO_RADAR_STATE_PATH="data/tibo_radar_state.json",
        TIBO_RADAR_BOOTSTRAP_SEND=False,
        TIBO_RADAR_APIFY_API_TOKEN=apify_token,
        TIBO_RADAR_APIFY_API_BASE_URL="https://api.apify.com",
        TIBO_RADAR_APIFY_ACTOR_ID="seemuapps~x-tweet-scraper",
        TIBO_RADAR_APIFY_MAX_ITEMS=25,
        TIBO_RADAR_APIFY_RUN_TIMEOUT_SECONDS=180,
    )


class TiboRadarFactoryTest(unittest.TestCase):
    def test_missing_api_key_disables_radar_without_starting_network_work(self):
        self.assertIsNone(build_tibo_radar(settings(), sender=Mock()))

    def test_configured_radar_targets_only_ai_xjtu_group(self):
        radar = build_tibo_radar(settings("secret"), sender=Mock())

        self.assertEqual(radar.group_id, 1105591264)
        self.assertEqual(radar.source.handle, "thsottiaux")

    def test_apify_provider_requires_its_own_token(self):
        self.assertIsNone(build_tibo_radar(settings(provider="apify"), sender=Mock()))

    def test_apify_provider_builds_without_twitterapi_key(self):
        radar = build_tibo_radar(
            settings(provider="apify", apify_token="apify-secret"), sender=Mock()
        )

        self.assertEqual(radar.group_id, 1105591264)
        self.assertEqual(radar.source.handle, "thsottiaux")
        self.assertEqual(radar.source.max_items, 25)


if __name__ == "__main__":
    unittest.main()
