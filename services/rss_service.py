# services/rss_service.py
from dataclasses import dataclass
from typing import List, Optional

import feedparser
import requests


@dataclass(frozen=True)
class RssEntry:
    """Normalized RSS entry data used by downstream bot flows."""

    title: str
    link: str
    published: str
    summary: str
    entry_id: str


class RssFetchError(RuntimeError):
    """Raised when an RSS feed cannot be fetched or parsed."""


def _entry_value(entry, key: str, default: str = "") -> str:
    value = entry.get(key, default)
    return value if isinstance(value, str) else default


def _normalize_entry(entry) -> RssEntry:
    link = _entry_value(entry, "link")
    entry_id = _entry_value(entry, "id") or _entry_value(entry, "guid") or link

    return RssEntry(
        title=_entry_value(entry, "title"),
        link=link,
        published=_entry_value(entry, "published"),
        summary=_entry_value(entry, "summary"),
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
