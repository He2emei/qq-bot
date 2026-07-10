# services/rss_filter_service.py
import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

import config
from services.rss_service import RssEntry, html_to_text


DEFAULT_KEYWORDS = ["Claude", "DeepSeek", "Codex", "Gemini", "Antigravity"]
SOURCE_IMPORTANT_CATEGORY = "要闻"
SOURCE_URL_RE = re.compile(r"https?://[^\s<>\"']+")
INTERNAL_SOURCE_HOSTS = {"mp.weixin.qq.com", "mmbiz.qpic.cn"}


@dataclass(frozen=True)
class RssNewsItem:
    number: int
    title: str
    url: str
    category: str
    content_text: str
    source_important: bool
    matched_keywords: List[str]

    @property
    def is_important(self) -> bool:
        return self.source_important or bool(self.matched_keywords)

    @property
    def important_reasons(self) -> List[str]:
        reasons = []
        if self.source_important:
            reasons.append("信息源要闻")
        reasons.extend(f"关键词:{keyword}" for keyword in self.matched_keywords)
        return reasons


@dataclass(frozen=True)
class RssFilterResult:
    entry: RssEntry
    keywords: List[str]
    all_items: List[RssNewsItem]
    important_items: List[RssNewsItem]
    other_items: List[RssNewsItem]


class RssKeywordStore:
    """Manage RSS important-news keywords."""

    def __init__(self, path: str = None):
        self.path = path or config.DATA_PATHS["rss_keywords"]

    def list_keywords(self) -> List[str]:
        data = self._load_data()
        keywords = data.get("keywords", [])
        return [keyword for keyword in keywords if isinstance(keyword, str) and keyword.strip()]

    def add_keywords(self, keywords: List[str]) -> List[str]:
        current = self.list_keywords()
        added = []

        for keyword in keywords:
            normalized = keyword.strip()
            if not normalized:
                continue
            if not _contains_case_insensitive(current, normalized):
                current.append(normalized)
                added.append(normalized)

        self._save_keywords(current)
        return added

    def delete_keywords(self, keywords: List[str]) -> List[str]:
        current = self.list_keywords()
        deleted = []
        delete_set = {keyword.lower() for keyword in keywords}
        remaining = []

        for keyword in current:
            if keyword.lower() in delete_set:
                deleted.append(keyword)
            else:
                remaining.append(keyword)

        self._save_keywords(remaining)
        return deleted

    def set_keywords(self, keywords: List[str]) -> List[str]:
        normalized_keywords = []
        for keyword in keywords:
            normalized = keyword.strip()
            if normalized and not _contains_case_insensitive(normalized_keywords, normalized):
                normalized_keywords.append(normalized)

        self._save_keywords(normalized_keywords)
        return normalized_keywords

    def replace_keyword(self, old_keyword: str, new_keyword: str) -> bool:
        old_normalized = old_keyword.strip()
        new_normalized = new_keyword.strip()
        if not old_normalized or not new_normalized:
            return False

        current = self.list_keywords()
        replaced = False
        updated = []

        for keyword in current:
            if keyword.lower() == old_normalized.lower():
                if not _contains_case_insensitive(updated, new_normalized):
                    updated.append(new_normalized)
                replaced = True
            elif keyword.lower() != new_normalized.lower():
                updated.append(keyword)

        if replaced:
            self._save_keywords(updated)

        return replaced

    def clear_keywords(self) -> None:
        self._save_keywords([])

    def _load_data(self) -> Dict:
        if not os.path.exists(self.path):
            self._save_keywords(DEFAULT_KEYWORDS)
            return {"keywords": DEFAULT_KEYWORDS}

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            data = {"keywords": DEFAULT_KEYWORDS}

        if not isinstance(data, dict):
            data = {"keywords": DEFAULT_KEYWORDS}
        return data

    def _save_keywords(self, keywords: List[str]) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump({"keywords": keywords}, file, ensure_ascii=False, indent=2)


def classify_rss_entry(entry: RssEntry, keywords: List[str] = None) -> RssFilterResult:
    """Split RSS news items into important and other buckets."""
    active_keywords = keywords if keywords is not None else rss_keyword_store.list_keywords()
    items = extract_news_items(entry, active_keywords)

    important_items = [item for item in items if item.is_important]
    other_items = [item for item in items if not item.is_important]

    return RssFilterResult(
        entry=entry,
        keywords=active_keywords,
        all_items=items,
        important_items=important_items,
        other_items=other_items,
    )


def extract_news_items(entry: RssEntry, keywords: List[str]) -> List[RssNewsItem]:
    soup = BeautifulSoup(entry.content_html, "html.parser")
    categories = _extract_overview_categories(soup)
    items = []

    for heading in soup.find_all("h2"):
        number = _extract_heading_number(heading)
        if number is None:
            continue

        title_link = heading.find("a")
        title = _compact_text(title_link.get_text(" ", strip=True) if title_link else heading.get_text(" ", strip=True))
        title = re.sub(r"\s*#\d+\s*$", "", title).strip()
        category = categories.get(number, "")
        section_html = _collect_section_html(heading)
        url = _extract_source_url(title_link, section_html)
        content_text = html_to_text(section_html)
        matched_keywords = _match_keywords(f"{title}\n{content_text}", keywords)

        items.append(
            RssNewsItem(
                number=number,
                title=title,
                url=url,
                category=category,
                content_text=content_text,
                source_important=category == SOURCE_IMPORTANT_CATEGORY,
                matched_keywords=matched_keywords,
            )
        )

    return sorted(items, key=lambda item: item.number)


def _extract_overview_categories(soup: BeautifulSoup) -> Dict[int, str]:
    categories = {}

    for heading in soup.find_all("h3"):
        category = _compact_text(heading.get_text(" ", strip=True))
        sibling = heading.find_next_sibling()
        while sibling is not None and sibling.name not in {"h2", "h3", "hr"}:
            for item in sibling.find_all("li"):
                number = _extract_item_number(item)
                if number is not None:
                    categories[number] = category
            sibling = sibling.find_next_sibling()

    return categories


def _extract_item_number(tag) -> int:
    text = tag.get_text(" ", strip=True)
    match = re.search(r"#(\d+)", text)
    return int(match.group(1)) if match else None


def _extract_heading_number(heading) -> int:
    code = heading.find("code")
    if code:
        match = re.search(r"#(\d+)", code.get_text(" ", strip=True))
        if match:
            return int(match.group(1))

    return _extract_item_number(heading)


def _collect_section_html(heading) -> str:
    parts = [str(heading)]
    sibling = heading.find_next_sibling()
    while sibling is not None and sibling.name != "h2":
        parts.append(str(sibling))
        sibling = sibling.find_next_sibling()
    return "\n".join(parts)


def _extract_source_url(title_link, section_html: str) -> str:
    if title_link:
        href = title_link.get("href", "").strip()
        if href:
            return href

    text = BeautifulSoup(section_html, "html.parser").get_text(" ", strip=True)
    for match in SOURCE_URL_RE.finditer(text):
        candidate = match.group(0).rstrip(".,;:!?)]}，。；：！？）】》")
        host = urlsplit(candidate).hostname
        if host and host not in INTERNAL_SOURCE_HOSTS:
            return candidate
    return ""


def _match_keywords(text: str, keywords: List[str]) -> List[str]:
    text_lower = text.lower()
    matched = []
    for keyword in keywords:
        normalized = keyword.strip()
        if normalized and normalized.lower() in text_lower:
            matched.append(normalized)
    return matched


def _contains_case_insensitive(values: List[str], target: str) -> bool:
    return target.lower() in {value.lower() for value in values}


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


rss_keyword_store = RssKeywordStore()
