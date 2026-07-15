from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

import config
from services.tibo_radar_factory import build_tibo_radar
from services.tibo_radar_stream import TwitterApiIoStreamWorker


def start_tibo_radar_scheduler():
    radar = build_tibo_radar()
    if radar is None:
        print("Tibo Radar 未配置 API key，调度器未启用", flush=True)
        return None

    def check_job():
        try:
            result = radar.check_and_push()
            if result.pushed_ids:
                print(f"[{datetime.now()}] Tibo Radar 已推送: {result.pushed_ids}", flush=True)
            elif result.seeded_ids:
                print(f"[{datetime.now()}] Tibo Radar 已建立初始水位: {result.seeded_ids}", flush=True)
            elif result.failed_ids:
                print(f"[{datetime.now()}] Tibo Radar 推送失败: {result.failed_ids}", flush=True)
        except Exception as exc:
            print(f"[{datetime.now()}] Tibo Radar 检查失败: {exc}", flush=True)

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_job,
        "interval",
        seconds=config.TIBO_RADAR_POLL_INTERVAL_SECONDS,
        timezone="Asia/Shanghai",
        id="check_tibo_radar_job",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    stream_worker = None
    if config.TIBO_RADAR_STREAM_ENABLED:
        stream_worker = TwitterApiIoStreamWorker(
            radar=radar,
            api_key=config.TIBO_RADAR_API_KEY,
            handle=config.TIBO_RADAR_HANDLE,
            base_url=config.TIBO_RADAR_API_BASE_URL,
            websocket_url=config.TIBO_RADAR_WEBSOCKET_URL,
            rule_tag=config.TIBO_RADAR_RULE_TAG,
            rule_interval_seconds=config.TIBO_RADAR_RULE_INTERVAL_SECONDS,
        )
        stream_worker.start()
    print(
        f"[{datetime.now()}] Tibo Radar 调度器已启动，目标群 {config.TIBO_RADAR_GROUP_ID}",
        flush=True,
    )
    return scheduler, stream_worker
