import re
from datetime import date, datetime
from html import unescape
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from services.ai_daily_source import DailyIssueCandidate, DailySourceError


HOME_URL = "https://www.bilibili.com/"
SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"
VIEW_URL = "https://api.bilibili.com/x/web-interface/view"
TITLE_DATE_RE = re.compile(r"【AI\s*早报\s*(\d{4}-\d{2}-\d{2})】")
WECHAT_URL_RE = re.compile(r"https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+")


class BilibiliDailySource:
    """Discover the latest AI Daily video and its linked WeChat article."""

    def __init__(self, uploader_mid, uploader_name, keyword, session=None, timeout=(5, 15)):
        self.uploader_mid = int(uploader_mid)
        self.uploader_name = uploader_name
        self.keyword = keyword
        self.session = session or requests.Session()
        self.timeout = timeout
        self._bootstrapped = False
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/138 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": f"https://search.bilibili.com/all?keyword={keyword}",
            }
        )

    def discover_latest(self) -> DailyIssueCandidate:
        videos = self._matching_videos()
        if not videos:
            raise DailySourceError("未找到目标账号的AI早报投稿")

        item = videos[0]
        article_url = self._article_url(item)
        if not article_url:
            raise DailySourceError(f"最新一期 {item.get('bvid', '')} 缺少微信链接")

        issue_date = self._issue_date(item["title"])
        return DailyIssueCandidate(
            title=item["title"],
            article_url=article_url,
            published_at=datetime.fromtimestamp(int(item["pubdate"]), ZoneInfo("Asia/Shanghai")),
            issue_date=issue_date,
            source_id=item["bvid"],
            video_url=self._video_url(item["bvid"]),
            discovered_by="bilibili",
        )

    def find_by_date(self, issue_date: date) -> str:
        for item in self._matching_videos():
            if self._issue_date(item["title"]) == issue_date:
                return self._video_url(item["bvid"])
        return ""

    def _matching_videos(self):
        data = self._request_data(
            SEARCH_URL,
            {
                "search_type": "video",
                "keyword": self.keyword,
                "order": "pubdate",
                "page": 1,
            },
        )
        result = data.get("result", []) if isinstance(data, dict) else []
        matches = []
        for raw in result:
            if not isinstance(raw, dict):
                continue
            item = dict(raw)
            item["title"] = BeautifulSoup(
                unescape(item.get("title", "")), "html.parser"
            ).get_text(" ", strip=True)
            if (
                item.get("mid") == self.uploader_mid
                and item.get("author") == self.uploader_name
                and TITLE_DATE_RE.search(item["title"])
            ):
                matches.append(item)
        return sorted(matches, key=lambda item: int(item.get("pubdate", 0)), reverse=True)

    def _article_url(self, item) -> str:
        match = WECHAT_URL_RE.search(item.get("description", ""))
        if match:
            return match.group(0)

        data = self._request_data(VIEW_URL, {"bvid": item.get("bvid", "")})
        match = WECHAT_URL_RE.search(data.get("desc", "") if isinstance(data, dict) else "")
        return match.group(0) if match else ""

    def _request_data(self, url: str, params: dict) -> dict:
        for attempt in range(2):
            self._bootstrap(reset=attempt == 1)
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                raise DailySourceError(f"B站请求失败: {type(exc).__name__}") from exc

            if response.status_code == 412 and attempt == 0:
                self._bootstrapped = False
                continue

            try:
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError, RuntimeError) as exc:
                raise DailySourceError(f"B站请求失败: {exc}") from exc

            if not isinstance(payload, dict) or payload.get("code") != 0:
                code = payload.get("code") if isinstance(payload, dict) else "invalid"
                raise DailySourceError(f"B站响应异常: code={code}")
            data = payload.get("data")
            if not isinstance(data, dict):
                raise DailySourceError("B站响应缺少 data 对象")
            return data

        raise DailySourceError("B站风控校验失败: HTTP 412")

    def _bootstrap(self, reset=False) -> None:
        if reset:
            self.session.cookies.clear()
            self._bootstrapped = False
        if self._bootstrapped:
            return

        try:
            response = self.session.get(HOME_URL, timeout=self.timeout)
            response.raise_for_status()
        except (requests.RequestException, RuntimeError) as exc:
            raise DailySourceError(f"B站匿名会话建立失败: {exc}") from exc
        self._bootstrapped = True

    @staticmethod
    def _issue_date(title: str) -> date:
        match = TITLE_DATE_RE.search(title)
        if not match:
            raise DailySourceError("投稿标题缺少AI早报日期")
        return date.fromisoformat(match.group(1))

    @staticmethod
    def _video_url(bvid: str) -> str:
        return f"https://www.bilibili.com/video/{bvid}/"
