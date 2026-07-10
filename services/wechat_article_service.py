import re
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

from services.rss_service import RssEntry, html_to_text


DATE_RE = re.compile(r"AI\s*早报\s*(\d{4}-\d{2}-\d{2})")
CANONICAL_RE = re.compile(r"^https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+")


class WechatArticleError(RuntimeError):
    """Raised when a WeChat article cannot be trusted as an AI Daily issue."""


class WechatArticleTransportError(WechatArticleError):
    """Raised for request or page-structure failures eligible for a later fallback."""


class WechatArticleService:
    def __init__(self, account_nickname, session=None, timeout=(5, 20)):
        self.account_nickname = account_nickname
        self.session = session or requests.Session()
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
                "Mobile Safari/537.36 MicroMessenger/8.0.49"
            )
        }

    def fetch(self, candidate) -> RssEntry:
        canonical_url = self._canonical_url(candidate.article_url)
        try:
            response = self.session.get(canonical_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise WechatArticleTransportError(f"微信文章获取失败: {exc}") from exc

        self._canonical_url(response.url)
        soup = BeautifulSoup(response.text, "html.parser")
        title_node = soup.select_one("#activity-name, .rich_media_title")
        account_node = soup.select_one("#js_name, .rich_media_meta_nickname")
        content_node = soup.select_one("#js_content")
        if not title_node or not content_node:
            raise WechatArticleTransportError("微信文章正文或标题缺失")

        account = account_node.get_text(" ", strip=True) if account_node else ""
        if account != self.account_nickname:
            raise WechatArticleError(f"微信公众号不匹配: {account}")

        article_title = title_node.get_text(" ", strip=True)
        date_match = DATE_RE.search(article_title)
        if not date_match or date_match.group(1) != candidate.issue_date.isoformat():
            raise WechatArticleError("微信文章日期不匹配")

        content_html = str(content_node)
        return RssEntry(
            title=candidate.issue_date.isoformat(),
            link=canonical_url,
            published=candidate.published_at.isoformat(),
            summary=article_title,
            content_html=content_html,
            content_text=html_to_text(content_html),
            entry_id=canonical_url,
            video_url=candidate.video_url,
            discovery_source=candidate.discovered_by,
        )

    @staticmethod
    def _canonical_url(url: str) -> str:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "mp.weixin.qq.com":
            raise WechatArticleError("只允许 HTTPS 微信文章域名 mp.weixin.qq.com")

        match = CANONICAL_RE.match(url)
        if not match:
            raise WechatArticleError("微信文章链接格式无效")
        return match.group(0)
