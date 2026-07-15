from typing import Optional

import config
from services.tibo_radar_service import TiboRadar, TiboRadarStateStore, TwitterApiIoSource
from utils.api_utils import send_group_message


def build_tibo_radar(settings=config, sender=send_group_message) -> Optional[TiboRadar]:
    api_key = getattr(settings, "TIBO_RADAR_API_KEY", "").strip()
    if not api_key:
        return None
    return TiboRadar(
        source=TwitterApiIoSource(
            api_key=api_key,
            handle=settings.TIBO_RADAR_HANDLE,
            base_url=settings.TIBO_RADAR_API_BASE_URL,
        ),
        state_store=TiboRadarStateStore(settings.TIBO_RADAR_STATE_PATH),
        sender=sender,
        group_id=settings.TIBO_RADAR_GROUP_ID,
        bootstrap_send=settings.TIBO_RADAR_BOOTSTRAP_SEND,
    )
