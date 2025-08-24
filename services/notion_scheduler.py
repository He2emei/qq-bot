# services/notion_scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
from services.notion_service import daily_manager
import time


def add_today_job():
    """添加今天的日记页面（带封面）"""
    try:
        print(f"[{datetime.now()}] 开始创建今日日记页面...")
        result = daily_manager.add_today_page(with_cover=True)
        print(f"[{datetime.now()}] 今日日记页面创建成功: {result['id']}")
    except Exception as e:
        print(f"[{datetime.now()}] 创建今日日记页面失败: {e}")


def add_next_week_job():
    """添加下周的页面（如果需要的话）"""
    try:
        print(f"[{datetime.now()}] 检查是否需要创建下周页面...")
        # 这里可以添加创建周页面的逻辑
        print(f"[{datetime.now()}] 下周页面检查完成")
    except Exception as e:
        print(f"[{datetime.now()}] 下周页面处理失败: {e}")


def update_daily_cover_job():
    """更新今日日记封面"""
    try:
        print(f"[{datetime.now()}] 开始更新今日日记封面...")
        success = daily_manager.update_daily_cover()
        if success:
            print(f"[{datetime.now()}] 今日日记封面更新成功")
        else:
            print(f"[{datetime.now()}] 今日日记封面更新失败")
    except Exception as e:
        print(f"[{datetime.now()}] 更新封面失败: {e}")


class NotionScheduler:
    """Notion 定时任务调度器"""

    def __init__(self, scheduler_type='background'):
        if scheduler_type == 'background':
            self.scheduler = BackgroundScheduler()
        else:
            self.scheduler = BlockingScheduler()

        self._setup_jobs()

    def _setup_jobs(self):
        """设置定时任务"""
        # 每天0:30创建今日日记页面
        self.scheduler.add_job(
            add_today_job,
            'cron',
            day='*/1',
            hour='0',
            minute='30',
            timezone='Asia/Shanghai',
            id='add_today_job'
        )

        # 每周日0:30检查下周页面
        self.scheduler.add_job(
            add_next_week_job,
            'cron',
            week='*/1',
            day_of_week='0',
            hour='0',
            minute='30',
            timezone='Asia/Shanghai',
            id='add_next_week_job'
        )

        # 每天8:00更新封面
        self.scheduler.add_job(
            update_daily_cover_job,
            'cron',
            day='*/1',
            hour='8',
            minute='0',
            timezone='Asia/Shanghai',
            id='update_cover_job'
        )

    def start(self):
        """启动调度器"""
        print(f"[{datetime.now()}] 启动 Notion 定时任务调度器...")
        self.scheduler.start()
        print(f"[{datetime.now()}] Notion 定时任务调度器已启动")

    def stop(self):
        """停止调度器"""
        print(f"[{datetime.now()}] 停止 Notion 定时任务调度器...")
        self.scheduler.shutdown()
        print(f"[{datetime.now()}] Notion 定时任务调度器已停止")

    def add_job(self, func, trigger, **kwargs):
        """添加自定义任务"""
        self.scheduler.add_job(func, trigger, **kwargs)

    def remove_job(self, job_id):
        """移除任务"""
        try:
            self.scheduler.remove_job(job_id)
            print(f"[{datetime.now()}] 任务 {job_id} 已移除")
        except Exception as e:
            print(f"[{datetime.now()}] 移除任务 {job_id} 失败: {e}")


# 全局调度器实例
notion_scheduler = NotionScheduler()

# 便捷函数
def start_notion_scheduler():
    """启动 Notion 调度器"""
    notion_scheduler.start()

def stop_notion_scheduler():
    """停止 Notion 调度器"""
    notion_scheduler.stop()