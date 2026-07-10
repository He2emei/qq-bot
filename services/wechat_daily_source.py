import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from services.ai_daily_source import DailyIssueCandidate, DailySourceError
from services.wechat_private_client import WechatPrivateApiError


TITLE_DATE_RE = re.compile(r"【AI\s*早报\s*(\d{4}-\d{2}-\d{2})】")


class WechatPrivateDailySource:
    """Adapt a private WeChat latest-articles response to a daily candidate."""

    def __init__(self, client, nickname: str, count: int = 5):
        self.client = client
        self.nickname = nickname
        self.count = count

    def discover_latest(self) -> DailyIssueCandidate:
        try:
            payload = self.client.get_latest_articles(self.nickname, count=self.count)
        except WechatPrivateApiError as exc:
            raise DailySourceError(str(exc)) from exc

        items = payload.get("data")
        if not isinstance(items, list):
            raise DailySourceError("微信最新文章响应缺少 data 列表")

        candidates = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("nickname") and item.get("nickname") != self.nickname:
                continue

            title = item.get("title", "")
            date_match = TITLE_DATE_RE.search(title)
            article_url = item.get("link") or item.get("url") or ""
            if not date_match or not article_url.startswith("https://mp.weixin.qq.com/s/"):
                continue

            try:
                published_at = datetime.fromtimestamp(
                    int(item.get("create_time")), ZoneInfo("Asia/Shanghai")
                )
            except (TypeError, ValueError, OSError):
                continue

            candidates.append(
                DailyIssueCandidate(
                    title=title,
                    article_url=article_url,
                    published_at=published_at,
                    issue_date=date.fromisoformat(date_match.group(1)),
                    source_id=article_url,
                    discovered_by="wechat_private",
                )
            )

        if not candidates:
            raise DailySourceError("微信私有接口未返回目标公众号的AI早报")
        return max(candidates, key=lambda candidate: candidate.published_at)
