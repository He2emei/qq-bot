# services/rss_scheduler.py
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

import config
from services.rss_push_service import check_and_push_latest_rss


def check_rss_update_job():
    """Poll AI Daily sources and push new content to pending groups."""
    try:
        print(f"[{datetime.now()}] 开始检查AI早报更新...", flush=True)
        result = check_and_push_latest_rss()
        if result.failed_group_ids:
            print(f"[{datetime.now()}] AI早报部分群推送失败: {result.failed_group_ids}", flush=True)
        if result.pushed:
            print(f"[{datetime.now()}] AI早报已推送: {result.title} -> {result.group_ids}", flush=True)
        elif not result.failed_group_ids:
            print(f"[{datetime.now()}] AI早报暂无新内容: {result.entry_id}", flush=True)
    except Exception as e:
        print(f"[{datetime.now()}] AI早报更新检查失败: {e}", flush=True)


class RssScheduler:
    """RSS polling scheduler."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        self.scheduler.add_job(
            check_rss_update_job,
            "interval",
            seconds=config.RSS_POLL_INTERVAL_SECONDS,
            timezone="Asia/Shanghai",
            id="check_rss_update_job",
            max_instances=1,
            coalesce=True,
        )

    def start(self):
        print(f"[{datetime.now()}] 启动 AI早报更新检查调度器...", flush=True)
        self.scheduler.start()
        print(f"[{datetime.now()}] AI早报更新检查调度器已启动", flush=True)

    def stop(self):
        print(f"[{datetime.now()}] 停止 AI早报更新检查调度器...", flush=True)
        self.scheduler.shutdown()
        print(f"[{datetime.now()}] AI早报更新检查调度器已停止", flush=True)


rss_scheduler = RssScheduler()


def start_rss_scheduler():
    rss_scheduler.start()


def stop_rss_scheduler():
    rss_scheduler.stop()
