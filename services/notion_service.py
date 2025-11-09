# services/notion_service.py
import requests
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
import json
import os
import time
import config


class NotionService:
    """Notion API 服务类"""

    def __init__(self, token_type="default"):
        self.base_url = "https://api.notion.com/v1/"
        self.token_type = token_type
        self._init_headers()
        self.session = requests.Session()
        if hasattr(config, 'NOTION_PROXY') and config.NOTION_PROXY:
            self.session.proxies = {"http": config.NOTION_PROXY, "https": config.NOTION_PROXY}
        # 设置默认超时时间
        self.timeout = 30
        self.max_retries = 3

    def _init_headers(self):
        """初始化请求头，根据token类型选择不同的token"""
        from dotenv import load_dotenv
        load_dotenv()

        import os
        if self.token_type == "diary":
            token = os.getenv("NOTION_TOKEN_DIARY", config.NOTION_TOKEN_DIARY)
        else:
            token = os.getenv("NOTION_TOKEN", config.NOTION_TOKEN)

        self.headers = {
            "Authorization": f"Bearer {token}",
            "notion-version": config.NOTION_VERSION
        }
        # print(self.headers)  # 注释掉调试输出

    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """带重试机制的请求方法"""
        kwargs.setdefault('timeout', self.timeout)

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.ConnectionError as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Connection failed after {self.max_retries} attempts: {e}")
                print(f"Connection attempt {attempt + 1} failed, retrying in 2 seconds...")
                time.sleep(2)
            except requests.exceptions.Timeout as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Request timeout after {self.max_retries} attempts: {e}")
                print(f"Request timeout attempt {attempt + 1}, retrying in 2 seconds...")
                time.sleep(2)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code >= 500:
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Server error after {self.max_retries} attempts: {e}")
                    print(f"Server error (status {e.response.status_code}) attempt {attempt + 1}, retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    # 对于客户端错误（如401，404），直接抛出
                    raise Exception(f"HTTP error: {e}")
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Request failed after {self.max_retries} attempts: {e}")
                print(f"Request attempt {attempt + 1} failed: {e}, retrying in 2 seconds...")
                time.sleep(2)

        raise Exception(f"Request failed after {self.max_retries} attempts")

    def _get_database_id(self, database_name: str) -> str:
        """获取数据库ID"""
        if database_name == "Daily Dairy 2.0":
            return config.NOTION_DATABASES['daily']
        elif database_name == "Weekly Dairy 2.0":
            return config.NOTION_DATABASES['weekly']
        elif database_name == "Terms Dairy 2.0":
            return config.NOTION_DATABASES['terms']
        else:
            raise ValueError(f"Unknown database: {database_name}")

    def query_database(self, database_name: str, filter_json: Optional[Dict] = None) -> Dict[str, Any]:
        """查询数据库"""
        database_id = self._get_database_id(database_name)
        url = f"{self.base_url}databases/{database_id}/query/"

        payload = {}
        if filter_json:
            payload = {"filter": filter_json}

        response = self._make_request_with_retry("POST", url, json=payload, verify=False)
        return response.json()

    def add_page(self, database_name: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加页面"""
        database_id = self._get_database_id(database_name)
        url = f"{self.base_url}pages/"

        # 确保 parent 设置正确
        page_data["parent"] = {
            "type": "database_id",
            "database_id": database_id
        }

        response = self._make_request_with_retry("POST", url, json=page_data)
        return response.json()

    def update_page(self, page_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新页面"""
        url = f"{self.base_url}pages/{page_id}"

        response = self._make_request_with_retry("PATCH", url, json=update_data)
        return response.json()

    def get_page_children(self, page_id: str) -> Dict[str, Any]:
        """获取页面子项"""
        url = f"{self.base_url}blocks/{page_id}/children"

        response = self._make_request_with_retry("GET", url)
        return response.json()


class NotionDailyManager:
    """每日日记管理器"""

    def __init__(self):
        self.notion_service = NotionService(token_type="diary")

    def get_today_date(self) -> date:
        """获取今日日期"""
        return datetime.now().date()

    def get_date_no_dash(self, dt: datetime) -> str:
        """获取没有'-'的日期字符串"""
        return dt.strftime("%Y%m%d")

    def date_dt2nt(self, dt: datetime) -> str:
        """datetime转Notion日期字符串"""
        return dt.strftime("%Y-%m-%d")

    def get_day_filter(self, target_date: datetime) -> Dict[str, Any]:
        """获取日期过滤器"""
        return {
            "property": "Date",
            "date": {
                "equals": self.date_dt2nt(target_date)
            }
        }

    def get_today_page(self) -> Optional[Dict[str, Any]]:
        """获取今天的日记页面"""
        today = datetime.now()
        filter_json = self.get_day_filter(today)

        try:
            result = self.notion_service.query_database("Daily Dairy 2.0", filter_json)
            if result["results"]:
                return result["results"][0]
        except requests.exceptions.ConnectionError as e:
            print(f"网络连接错误，无法获取今日日记页面: {e}")
        except requests.exceptions.Timeout as e:
            print(f"请求超时，无法获取今日日记页面: {e}")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP错误，无法获取今日日记页面: {e}")
        except Exception as e:
            print(f"获取今日日记页面时出现未知错误: {e}")

        return None

    def add_today_page(self, with_cover: bool = False) -> Dict[str, Any]:
        """添加今天的日记页面"""
        today = datetime.now()

        # 构建页面数据
        page_data = {
            "properties": {
                "Date": {
                    "type": "date",
                    "date": {
                        "start": self.date_dt2nt(today)
                    }
                },
                "Name": {
                    "type": "title",
                    "title": [
                        {
                            "type": "mention",
                            "mention": {
                                "type": "date",
                                "date": {
                                    "start": self.date_dt2nt(today)
                                }
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": f" {self.get_date_no_dash(today)}"
                            }
                        }
                    ]
                }
            }
        }

        # 如果需要封面，添加Bing壁纸
        if with_cover:
            try:
                from utils.notion_utils import get_bing_image_url
                page_data["cover"] = {
                    "type": "external",
                    "external": {
                        "url": get_bing_image_url()
                    }
                }
            except Exception as e:
                print(f"Error getting Bing image: {e}")
                # 使用默认图片
                page_data["cover"] = {
                    "type": "external",
                    "external": {
                        "url": "https://picsum.photos/800/600?random=1"
                    }
                }

        try:
            result = self.notion_service.add_page("Daily Dairy 2.0", page_data)
            print(f"Added today page: {self.date_dt2nt(today)}")
            return result
        except Exception as e:
            print(f"Error adding today page: {e}")
            raise

    def update_daily_cover(self) -> bool:
        """更新今日日记封面"""
        try:
            from utils.notion_utils import get_bing_image_url

            today_page = self.get_today_page()
            if not today_page:
                print("No today page found to update")
                return False

            update_data = {
                "cover": {
                    "type": "external",
                    "external": {
                        "url": get_bing_image_url()
                    }
                }
            }

            result = self.notion_service.update_page(today_page["id"], update_data)
            print(f"Updated cover for page: {today_page['id']}")
            return True

        except Exception as e:
            print(f"Error updating daily cover: {e}")
            return False


class NotionWeeklyManager:
    """每周周记管理器"""

    def __init__(self):
        self.notion_service = NotionService(token_type="diary")

    def get_week_filter(self, week_name: str) -> Dict[str, Any]:
        """获取周页面过滤器"""
        return {
            "property": "Name",
            "rich_text": {
                "equals": week_name
            }
        }

    def get_week_page(self, week_name: str) -> Optional[Dict[str, Any]]:
        """获取指定周的页面"""
        try:
            filter_json = self.get_week_filter(week_name)
            result = self.notion_service.query_database("Weekly Dairy 2.0", filter_json)
            if result["results"]:
                return result["results"][0]
        except Exception as e:
            print(f"获取周页面失败: {e}")

        return None

    def add_week_page(self, week_name: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """添加周页面"""
        # 直接使用daily_manager中的方法，避免重复导入
        date_dt2nt = daily_manager.date_dt2nt

        page_data = {
            "properties": {
                "Date": {
                    "type": "date",
                    "date": {
                        "start": date_dt2nt(start_date),
                        "end": date_dt2nt(end_date)
                    }
                },
                "Name": {
                    "type": "title",
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": week_name,
                                "link": None
                            },
                            "href": None
                        }
                    ]
                }
            }
        }

        try:
            result = self.notion_service.add_page("Weekly Dairy 2.0", page_data)
            print(f"添加周页面成功: {week_name}")
            return result
        except Exception as e:
            print(f"添加周页面失败: {e}")
            raise

    def check_and_create_current_week(self) -> bool:
        """检查并创建当前周页面"""
        from utils.notion_utils import get_term, get_week_num, wk_name, certain_weekday

        try:
            # 获取当前学期和周信息
            current_term = get_term()
            if not current_term:
                print("无法获取当前学期信息")
                return False

            week_num = get_week_num()
            week_name = wk_name()

            # 检查周页面是否已存在
            existing_page = self.get_week_page(week_name)
            if existing_page:
                print(f"周页面已存在: {week_name}")
                return True

            # 计算周的开始和结束日期
            term_start = current_term['start']
            week_start = term_start + timedelta(days=(week_num - 1) * 7)
            week_end = week_start + timedelta(days=6)

            # 创建周页面
            self.add_week_page(week_name, week_start, week_end)
            return True

        except Exception as e:
            print(f"检查并创建当前周页面失败: {e}")
            return False


# 全局服务实例
notion_service = NotionService()
daily_manager = NotionDailyManager()
weekly_manager = NotionWeeklyManager()
