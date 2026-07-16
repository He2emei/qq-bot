from typing import Optional

import config
from services.apify_tibo_source import ApifyTiboSource
from services.tibo_radar_service import TiboRadar, TiboRadarStateStore, TwitterApiIoSource
from utils.api_utils import send_group_message


def build_tibo_radar(settings=config, sender=send_group_message) -> Optional[TiboRadar]:
    provider = getattr(settings, "TIBO_RADAR_PROVIDER", "twitterapi").strip().lower()
    if provider == "apify":
        api_token = getattr(settings, "TIBO_RADAR_APIFY_API_TOKEN", "").strip()
        if not api_token:
            return None
        source = ApifyTiboSource(
            api_token=api_token,
            handle=settings.TIBO_RADAR_HANDLE,
            actor_id=settings.TIBO_RADAR_APIFY_ACTOR_ID,
            base_url=settings.TIBO_RADAR_APIFY_API_BASE_URL,
            max_items=settings.TIBO_RADAR_APIFY_MAX_ITEMS,
            run_timeout_seconds=settings.TIBO_RADAR_APIFY_RUN_TIMEOUT_SECONDS,
        )
    elif provider == "twitterapi":
        api_key = getattr(settings, "TIBO_RADAR_API_KEY", "").strip()
        if not api_key:
            return None
        source = TwitterApiIoSource(
            api_key=api_key,
            handle=settings.TIBO_RADAR_HANDLE,
            base_url=settings.TIBO_RADAR_API_BASE_URL,
        )
    else:
        raise ValueError(f"不支持的 Tibo Radar provider: {provider}")

    return TiboRadar(
        source=source,
        state_store=TiboRadarStateStore(settings.TIBO_RADAR_STATE_PATH),
        sender=sender,
        group_id=settings.TIBO_RADAR_GROUP_ID,
        bootstrap_send=settings.TIBO_RADAR_BOOTSTRAP_SEND,
    )
