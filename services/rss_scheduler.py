# services/rss_scheduler.py
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

import config
from services.rss_push_service import check_and_push_latest_rss


def check_rss_update_job():
    """Poll RSS and push when a new entry appears."""
    try:
        print(f"[{datetime.now()}] 开始检查RSS更新...")
        result = check_and_push_latest_rss()
        if result.pushed:
            print(f"[{datetime.now()}] RSS新条目已推送: {result.title} -> {result.group_ids}")
        else:
            print(f"[{datetime.now()}] RSS暂无新条目: {result.entry_id}")
    except Exception as e:
        print(f"[{datetime.now()}] RSS更新检查失败: {e}")


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
        print(f"[{datetime.now()}] 启动 RSS 更新检查调度器...")
        self.scheduler.start()
        print(f"[{datetime.now()}] RSS 更新检查调度器已启动")

    def stop(self):
        print(f"[{datetime.now()}] 停止 RSS 更新检查调度器...")
        self.scheduler.shutdown()
        print(f"[{datetime.now()}] RSS 更新检查调度器已停止")


rss_scheduler = RssScheduler()


def start_rss_scheduler():
    rss_scheduler.start()


def stop_rss_scheduler():
    rss_scheduler.stop()
