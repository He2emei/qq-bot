# services/rss_push_service.py
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import config
from services.rss_display_service import build_other_news_forward_nodes, format_important_news_message
from services.rss_filter_service import classify_rss_entry
from services.rss_service import RssEntry, fetch_rss_entries
from utils.api_utils import send_group_forward_message, send_group_message


@dataclass(frozen=True)
class RssPushResult:
    pushed: bool
    entry_id: str
    title: str
    group_ids: List[int]


class RssPushStateStore:
    """Persist last pushed RSS entry state."""

    def __init__(self, path: str = None):
        self.path = path or config.DATA_PATHS["rss_state"]

    def get_last_entry_id(self) -> str:
        data = self._load_data()
        return data.get("last_entry_id", "")

    def mark_pushed(self, entry: RssEntry) -> None:
        self._save_data(
            {
                "last_entry_id": entry.entry_id,
                "last_title": entry.title,
                "last_link": entry.link,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )

    def _load_data(self) -> Dict:
        if not os.path.exists(self.path):
            return {}

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            return {}

        return data if isinstance(data, dict) else {}

    def _save_data(self, data: Dict) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)


def check_and_push_latest_rss(force: bool = False) -> RssPushResult:
    """Fetch the latest RSS entry and push it when it has not been sent."""
    entries = fetch_rss_entries(config.RSS_FEED_URL, limit=1)
    if not entries:
        return RssPushResult(False, "", "", [])

    entry = entries[0]
    last_entry_id = rss_push_state_store.get_last_entry_id()
    if not force and last_entry_id == entry.entry_id:
        print(f"RSS无新条目，跳过推送: {entry.entry_id}", flush=True)
        return RssPushResult(False, entry.entry_id, entry.title, [])

    push_rss_entry(entry, config.RSS_PUSH_GROUP_IDS)
    rss_push_state_store.mark_pushed(entry)
    return RssPushResult(True, entry.entry_id, entry.title, list(config.RSS_PUSH_GROUP_IDS))


def push_rss_entry(entry: RssEntry, group_ids: List[int]) -> None:
    result = classify_rss_entry(entry)
    important_message = format_important_news_message(result)
    forward_nodes = build_other_news_forward_nodes(
        result,
        bot_user_id=config.RSS_FORWARD_USER_ID,
        bot_nickname=config.RSS_SOURCE_NAME,
    )

    for group_id in group_ids:
        send_group_message(group_id, important_message)
        send_group_forward_message(group_id, forward_nodes)


rss_push_state_store = RssPushStateStore()
