# services/rss_service.py
from dataclasses import dataclass
import re
from typing import List, Optional

from bs4 import BeautifulSoup
import feedparser
import requests


@dataclass(frozen=True)
class RssEntry:
    """Normalized RSS entry data used by downstream bot flows."""

    title: str
    link: str
    published: str
    summary: str
    content_html: str
    content_text: str
    entry_id: str


class RssFetchError(RuntimeError):
    """Raised when an RSS feed cannot be fetched or parsed."""


def _entry_value(entry, key: str, default: str = "") -> str:
    value = entry.get(key, default)
    return value if isinstance(value, str) else default


def html_to_text(html: str) -> str:
    """Convert RSS HTML content into readable plain text for QQ messages."""
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    for link in soup.find_all("a"):
        href = link.get("href", "").strip()
        text = link.get_text(strip=True)
        if href and text and href != text:
            link.replace_with(f"{text} ({href})")
        elif href and not text:
            link.replace_with(href)

    lines = []
    block_tags = {"h1", "h2", "h3", "h4", "p", "li", "blockquote", "hr", "img"}

    for tag in soup.find_all(block_tags):
        if tag.name != "img" and tag.find_parent(["li", "blockquote"]):
            continue

        if tag.name == "img":
            image_url = tag.get("src", "").strip()
            text = f"[图片] {image_url}" if image_url else "[图片]"
        elif tag.name == "hr":
            text = "-" * 24
        else:
            text = tag.get_text(" ", strip=True)

        text = _compact_text(text)
        if not text:
            continue

        if tag.name == "li":
            text = f"- {text}"
        elif tag.name == "blockquote":
            text = f"> {text}"

        lines.append(text)

    return "\n\n".join(lines).strip()


def _compact_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([：，。；、？！）】》])", r"\1", text)
    text = re.sub(r"([（【《])\s+", r"\1", text)
    text = re.sub(r"([：])\s+", r"\1", text)
    return text


def _entry_content_html(entry) -> str:
    content_items = entry.get("content", [])
    if content_items:
        first_content = content_items[0]
        if isinstance(first_content, dict):
            return first_content.get("value", "")

    return _entry_value(entry, "summary")


def _normalize_entry(entry) -> RssEntry:
    link = _entry_value(entry, "link")
    entry_id = _entry_value(entry, "id") or _entry_value(entry, "guid") or link
    content_html = _entry_content_html(entry)

    return RssEntry(
        title=_entry_value(entry, "title"),
        link=link,
        published=_entry_value(entry, "published"),
        summary=_entry_value(entry, "summary"),
        content_html=content_html,
        content_text=html_to_text(content_html),
        entry_id=entry_id,
    )


def fetch_rss_entries(feed_url: str, limit: Optional[int] = None, timeout: int = 15) -> List[RssEntry]:
    """Fetch an RSS/Atom feed and return normalized entries."""
    try:
        response = requests.get(feed_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RssFetchError(f"RSS源获取失败: {feed_url} - {exc}") from exc

    parsed_feed = feedparser.parse(response.content)
    if parsed_feed.bozo:
        bozo_exception = getattr(parsed_feed, "bozo_exception", None)
        raise RssFetchError(f"RSS源解析失败: {feed_url} - {bozo_exception}")

    entries = [_normalize_entry(entry) for entry in parsed_feed.entries]
    if limit is not None:
        return entries[:limit]
    return entries
