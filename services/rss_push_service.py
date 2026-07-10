import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import Dict, List, Set, Tuple

import config
from services.ai_daily_factory import build_ai_daily_runtime
from services.rss_display_service import build_other_news_forward_nodes, format_important_news_message
from services.rss_filter_service import classify_rss_entry
from services.rss_service import RssEntry
from utils.api_utils import send_group_forward_message, send_group_message


class RssPushError(RuntimeError):
    """Raised when a candidate AI Daily cannot be safely pushed."""


@dataclass(frozen=True)
class RssPushResult:
    pushed: bool
    entry_id: str
    title: str
    group_ids: List[int]
    failed_group_ids: List[int] = field(default_factory=list)


class RssPushStateStore:
    """Persist per-group AI Daily delivery state with legacy RSS migration."""

    def __init__(self, path: str = None):
        self.path = path or config.DATA_PATHS["rss_state"]

    def completed_groups(self, entry_id: str, configured_groups: List[int]) -> Set[int]:
        data = self._load_data()
        if data.get("last_entry_id") == entry_id and not data.get("entry_id"):
            data = {
                "entry_id": entry_id,
                "title": data.get("last_title", ""),
                "article_url": data.get("last_link", ""),
                "video_url": "",
                "groups": {
                    str(group_id): datetime.now().isoformat(timespec="seconds")
                    for group_id in configured_groups
                },
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
            self._save_data(data)
            return set(configured_groups)

        if data.get("entry_id") != entry_id:
            return set()

        groups = data.get("groups", {})
        if not isinstance(groups, dict):
            return set()
        completed = set()
        for group_id in groups:
            try:
                completed.add(int(group_id))
            except (TypeError, ValueError):
                continue
        return completed

    def mark_group_pushed(self, entry: RssEntry, group_id: int) -> None:
        data = self._load_data()
        if data.get("entry_id") != entry.entry_id:
            data = {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "article_url": entry.link,
                "video_url": entry.video_url,
                "groups": {},
            }
        if not isinstance(data.get("groups"), dict):
            data["groups"] = {}
        data["groups"][str(group_id)] = datetime.now().isoformat(timespec="seconds")
        data["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self._save_data(data)

    def _load_data(self) -> Dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"AI早报状态读取失败，将从空状态恢复: {exc}", flush=True)
            return {}
        return data if isinstance(data, dict) else {}

    def _save_data(self, data: Dict) -> None:
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        temp_path = ""
        try:
            with NamedTemporaryFile("w", encoding="utf-8", dir=directory, delete=False) as file:
                temp_path = file.name
                json.dump(data, file, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)


def check_and_push_latest_rss(
    force: bool = False,
    group_ids: List[int] = None,
    runtime=None,
    state_store: RssPushStateStore = None,
) -> RssPushResult:
    """Discover, validate and push the latest AI Daily to pending groups."""
    runtime = runtime or ai_daily_runtime
    state_store = state_store or rss_push_state_store
    target_groups = list(group_ids if group_ids is not None else config.RSS_PUSH_GROUP_IDS)

    candidate = runtime.discovery.discover_latest()
    entry = runtime.article_service.fetch(candidate)
    completed = state_store.completed_groups(entry.entry_id, target_groups)
    pending_groups = target_groups if force else [
        group_id for group_id in target_groups if group_id not in completed
    ]
    if not pending_groups:
        return RssPushResult(False, entry.entry_id, entry.title, [])

    sent_groups, failed_groups = push_rss_entry(entry, pending_groups, state_store)
    return RssPushResult(
        bool(sent_groups),
        entry.entry_id,
        entry.title,
        sent_groups,
        failed_groups,
    )


def push_rss_entry(
    entry: RssEntry,
    group_ids: List[int],
    state_store: RssPushStateStore = None,
) -> Tuple[List[int], List[int]]:
    """Push one entry to groups and mark only fully delivered groups complete."""
    state_store = state_store or rss_push_state_store
    result = classify_rss_entry(entry)
    if not result.all_items:
        raise RssPushError("AI早报没有解析到新闻条目，拒绝推送")

    important_message = format_important_news_message(result)
    forward_nodes = build_other_news_forward_nodes(
        result,
        bot_user_id=config.RSS_FORWARD_USER_ID,
        bot_nickname=config.RSS_SOURCE_NAME,
    )
    sent_groups = []
    failed_groups = []
    for group_id in group_ids:
        if not send_group_message(group_id, important_message):
            failed_groups.append(group_id)
            continue
        if not send_group_forward_message(group_id, forward_nodes):
            failed_groups.append(group_id)
            continue
        state_store.mark_group_pushed(entry, group_id)
        sent_groups.append(group_id)

    return sent_groups, failed_groups


rss_push_state_store = RssPushStateStore()
ai_daily_runtime = build_ai_daily_runtime()
