# services/rss_display_service.py
from collections import OrderedDict
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

import config
from services.rss_filter_service import RssFilterResult


WEEKDAY_NAMES = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def format_important_news_message(result: RssFilterResult) -> str:
    """Build the plain group message for important RSS news."""
    date_text = _format_entry_date(result.entry.title)
    lines = [f"今天是{date_text}，为您带来今日AI早报："]

    if result.important_items:
        for item in result.important_items:
            lines.append(f"{item.number}. {item.title}")
    else:
        lines.append("今日暂无重点新闻。")

    return "\n".join(lines)


def build_other_news_forward_nodes(result: RssFilterResult, bot_user_id: int, bot_nickname: str = None) -> List[dict]:
    """Build custom forward-message nodes for RSS categories."""
    nickname = bot_nickname or config.RSS_SOURCE_NAME
    nodes = [_make_forward_node(bot_user_id, nickname, _format_source_info(result))]

    for category, items in _group_items_by_category(result).items():
        content = _format_category_items(category, items)
        if content:
            nodes.append(_make_forward_node(bot_user_id, nickname, content))

    return nodes


def _format_entry_date(title: str) -> str:
    try:
        entry_date = datetime.strptime(title, "%Y-%m-%d").date()
        return f"{entry_date.year}年{entry_date.month:02d}月{entry_date.day:02d}日，{WEEKDAY_NAMES[entry_date.weekday()]}"
    except ValueError:
        return title


def _format_source_info(result: RssFilterResult) -> str:
    bilibili_url = _extract_bilibili_url(result.entry.content_html)
    lines = [
        f"今日AI早报来源：{config.RSS_SOURCE_NAME}",
        f"原文链接：{result.entry.link}",
    ]

    if bilibili_url:
        lines.append(f"哔哩哔哩视频版：{bilibili_url}")

    lines.extend(
        [
            f"作者主页：{config.RSS_SOURCE_URL}",
            f"欢迎关注原作者：{config.RSS_SOURCE_NAME}",
        ]
    )
    return "\n".join(lines)


def _extract_bilibili_url(content_html: str) -> Optional[str]:
    soup = BeautifulSoup(content_html, "html.parser")
    for link in soup.find_all("a"):
        href = link.get("href", "").strip()
        text = link.get_text(" ", strip=True)
        if "bilibili.com" in href or "哔哩哔哩" in text:
            return href
    return None


def _group_items_by_category(result: RssFilterResult) -> OrderedDict:
    grouped = OrderedDict()
    for item in result.all_items:
        category = item.category or "未分类"
        grouped.setdefault(category, []).append(item)
    return grouped


def _format_category_items(category: str, items: List) -> str:
    lines = [f"【{category}】"]
    for item in items:
        lines.append("")
        lines.append(f"#{item.number} {item.title}")
        if item.url:
            lines.append(item.url)
    return "\n".join(lines)


def _make_forward_node(user_id: int, nickname: str, text: str) -> dict:
    return {
        "type": "node",
        "data": {
            "user_id": str(user_id),
            "nickname": nickname,
            "content": [
                {
                    "type": "text",
                    "data": {
                        "text": text,
                    },
                }
            ],
        },
    }
