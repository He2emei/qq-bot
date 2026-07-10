import re
from html import escape
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

from services.rss_service import RssEntry, html_to_text


DATE_RE = re.compile(r"AI\s*早报\s*(\d{4}-\d{2}-\d{2})")
CANONICAL_RE = re.compile(r"^https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
MARKDOWN_NUMBER_RE = re.compile(r"\s*(#\d+)\s*$")


class WechatArticleError(RuntimeError):
    """Raised when a WeChat article cannot be trusted as an AI Daily issue."""


class WechatArticleTransportError(WechatArticleError):
    """Raised for request or page-structure failures eligible for a later fallback."""


class WechatArticleService:
    def __init__(self, account_nickname, session=None, timeout=(5, 20), markdown_extractor=None):
        self.account_nickname = account_nickname
        self.session = session or requests.Session()
        self.timeout = timeout
        self.markdown_extractor = markdown_extractor
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
                "Mobile Safari/537.36 MicroMessenger/8.0.49"
            )
        }

    def fetch(self, candidate) -> RssEntry:
        canonical_url = self._canonical_url(candidate.article_url)
        try:
            return self._fetch_html(candidate, canonical_url)
        except WechatArticleTransportError:
            if self.markdown_extractor is None:
                raise
            markdown = self.markdown_extractor(canonical_url)
            return self._from_markdown(candidate, canonical_url, markdown)

    def _fetch_html(self, candidate, canonical_url: str) -> RssEntry:
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

    def _from_markdown(self, candidate, canonical_url: str, markdown: str) -> RssEntry:
        if not isinstance(markdown, str) or not markdown.strip():
            raise WechatArticleTransportError("微信私有接口未返回 Markdown 正文")

        date_match = DATE_RE.search(markdown)
        if not date_match or date_match.group(1) != candidate.issue_date.isoformat():
            raise WechatArticleError("微信 Markdown 文章日期不匹配")

        content_html = markdown_to_content_html(markdown)
        return RssEntry(
            title=candidate.issue_date.isoformat(),
            link=canonical_url,
            published=candidate.published_at.isoformat(),
            summary=f"AI 早报 {candidate.issue_date.isoformat()}",
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


def markdown_to_content_html(markdown: str) -> str:
    """Keep the heading structure consumed by the existing RSS classifier."""
    parts = []
    overview_open = False
    list_open = False

    def close_list():
        nonlocal list_open
        if list_open:
            parts.append("</ul>")
            list_open = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line or set(line) <= {"=", "-"}:
            continue

        if line.startswith("### "):
            close_list()
            parts.append(f"<h3>{_markdown_inline_html(line[4:])}</h3>")
            continue

        if line.startswith("## "):
            close_list()
            heading = line[3:].strip()
            overview_open = heading == "概览"
            if overview_open:
                parts.append("<h2>概览</h2>")
            else:
                parts.append(f"<h2>{_markdown_headline_html(heading)}</h2>")
            continue

        if line.startswith("# "):
            close_list()
            overview_open = False
            parts.append(f"<h1>{_markdown_inline_html(line[2:])}</h1>")
            continue

        if overview_open and (line.startswith(("- ", "* ")) or "#" in line):
            if not list_open:
                parts.append("<ul>")
                list_open = True
            parts.append(f"<li>{_markdown_inline_html(line[2:] if line[:2] in {'- ', '* '} else line)}</li>")
            continue

        close_list()
        parts.append(f"<p>{_markdown_inline_html(line)}</p>")

    close_list()
    return "\n".join(parts)


def _markdown_headline_html(text: str) -> str:
    match = MARKDOWN_NUMBER_RE.search(text)
    if not match:
        return _markdown_inline_html(text)
    return f"{_markdown_inline_html(text[:match.start()])} <code>{escape(match.group(1))}</code>"


def _markdown_inline_html(text: str) -> str:
    parts = []
    position = 0
    for match in MARKDOWN_LINK_RE.finditer(text):
        parts.append(_escape_markdown_text(text[position:match.start()]))
        parts.append(
            f'<a href="{escape(match.group(2), quote=True)}">'
            f"{_escape_markdown_text(match.group(1))}</a>"
        )
        position = match.end()
    parts.append(_escape_markdown_text(text[position:]))
    return "".join(parts)


def _escape_markdown_text(text: str) -> str:
    return escape(re.sub(r"[`*_]", "", text))
