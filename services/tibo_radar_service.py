import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from tempfile import NamedTemporaryFile
from typing import Callable, List

import requests

try:
    import fcntl
except ImportError:  # Windows test/development host
    fcntl = None


class TiboSourceError(RuntimeError):
    """Raised when the configured Tibo source cannot return valid data."""


@dataclass(frozen=True)
class TiboPost:
    post_id: str
    text: str
    created_at: datetime
    url: str
    is_reply: bool = False


@dataclass(frozen=True)
class TiboRadarResult:
    seeded_ids: List[str] = field(default_factory=list)
    pushed_ids: List[str] = field(default_factory=list)
    failed_ids: List[str] = field(default_factory=list)


def parse_tibo_datetime(value: str) -> datetime:
    if not value:
        raise TiboSourceError("帖子缺少创建时间")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError) as exc:
            raise TiboSourceError(f"无法解析帖子时间: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class TwitterApiIoSource:
    """Fetch incremental public posts through TwitterAPI.io advanced search."""

    def __init__(
        self,
        api_key: str,
        handle: str,
        base_url: str = "https://api.twitterapi.io",
        session=None,
        timeout=(5, 15),
    ):
        self.api_key = api_key
        self.handle = handle.lstrip("@")
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_since(self, since: datetime, until: datetime) -> List[TiboPost]:
        posts = []
        windows = [(since, until)]
        request_number = 0
        while windows:
            window_since, window_until = windows.pop(0)
            request_number += 1
            if request_number > 64:
                raise TiboSourceError("TwitterAPI.io 时间窗口拆分超过安全上限")
            query = (
                f"from:{self.handle} -filter:nativeretweets "
                f"since_time:{int(window_since.timestamp())} "
                f"until_time:{int(window_until.timestamp())}"
            )
            try:
                response = self.session.get(
                    f"{self.base_url}/twitter/tweet/advanced_search",
                    headers={"X-API-Key": self.api_key},
                    params={"query": query, "queryType": "Latest"},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                raise TiboSourceError(f"TwitterAPI.io 请求失败: {type(exc).__name__}") from exc

            raw_posts = payload.get("tweets", []) if isinstance(payload, dict) else []
            response_headers = getattr(response, "headers", {})
            credits = (
                response_headers.get("x-credits-used")
                or response_headers.get("x-credit-cost")
                or (payload.get("credits_used") if isinstance(payload, dict) else None)
                or "unknown"
            )
            print(
                f"Tibo Radar advanced_search request={request_number} "
                f"tweets={len(raw_posts)} credits={credits}",
                flush=True,
            )

            if payload.get("has_next_page"):
                span = window_until - window_since
                if span <= timedelta(seconds=1):
                    raise TiboSourceError("TwitterAPI.io 单秒时间窗口结果仍超过上限")
                midpoint = window_since + span / 2
                windows[0:0] = [
                    (window_since, midpoint),
                    (midpoint, window_until),
                ]
                continue

            for item in raw_posts:
                if not isinstance(item, dict):
                    continue
                post_id = str(item.get("id", "")).strip()
                text = str(item.get("text", "")).strip()
                if not post_id or not text:
                    continue
                posts.append(
                    TiboPost(
                        post_id=post_id,
                        text=text,
                        created_at=parse_tibo_datetime(str(item.get("createdAt", ""))),
                        url=str(item.get("url") or f"https://x.com/{self.handle}/status/{post_id}"),
                        is_reply=bool(item.get("isReply")),
                    )
                )

        deduplicated = {post.post_id: post for post in posts}
        return sorted(deduplicated.values(), key=lambda item: (item.created_at, item.post_id))


class TiboRadarStateStore:
    """Persist per-post, per-group delivery state atomically."""

    def __init__(self, path: str):
        self.path = path

    def load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def is_initialized(self) -> bool:
        return bool(self.load().get("initialized"))

    def query_since(self, now: datetime) -> datetime:
        value = self.load().get("last_checked_at")
        if not value:
            return now - timedelta(hours=24)
        return parse_tibo_datetime(value) - timedelta(minutes=5)

    def is_completed(self, post_id: str, group_id: int) -> bool:
        deliveries = self.load().get("deliveries", {})
        return str(group_id) in deliveries.get(str(post_id), {})

    def mark_completed(self, post: TiboPost, group_id: int, now: datetime) -> None:
        data = self.load()
        deliveries = data.setdefault("deliveries", {})
        groups = deliveries.setdefault(post.post_id, {})
        groups[str(group_id)] = now.isoformat()
        data.setdefault("pending", {}).pop(post.post_id, None)
        self._save(data)

    def enqueue_pending(self, posts: List[TiboPost], received_at: datetime) -> None:
        data = self.load()
        pending = data.setdefault("pending", {})
        received = data.setdefault("received_at", {})
        for post in posts:
            received.setdefault(post.post_id, received_at.isoformat())
            pending.setdefault(
                post.post_id,
                {
                    "text": post.text,
                    "created_at": post.created_at.isoformat(),
                    "url": post.url,
                    "is_reply": post.is_reply,
                    "received_at": received_at.isoformat(),
                },
            )
        self._save(data)

    def pending_posts(self) -> List[TiboPost]:
        posts = []
        for post_id, item in self.load().get("pending", {}).items():
            try:
                posts.append(
                    TiboPost(
                        post_id=str(post_id),
                        text=str(item["text"]),
                        created_at=parse_tibo_datetime(str(item["created_at"])),
                        url=str(item["url"]),
                        is_reply=bool(item.get("is_reply")),
                    )
                )
            except (KeyError, TypeError, TiboSourceError):
                continue
        return posts

    def mark_checked(self, now: datetime) -> None:
        data = self.load()
        data["initialized"] = True
        data["last_checked_at"] = now.isoformat()
        deliveries = data.get("deliveries", {})
        if len(deliveries) > 500:
            data["deliveries"] = dict(list(deliveries.items())[-500:])
        self._save(data)

    def seed(self, posts: List[TiboPost], group_id: int, now: datetime) -> None:
        data = self.load()
        deliveries = data.setdefault("deliveries", {})
        for post in posts:
            deliveries.setdefault(post.post_id, {})[str(group_id)] = now.isoformat()
        data["initialized"] = True
        data["last_checked_at"] = now.isoformat()
        self._save(data)

    def try_lock(self, blocking: bool = False):
        return _StateFileLock(f"{self.path}.lock", blocking=blocking)

    def try_stream_lock(self):
        return _StateFileLock(f"{self.path}.stream.lock")

    def _save(self, data: dict) -> None:
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


def format_tibo_post(post: TiboPost) -> str:
    kind = "回复" if post.is_reply else "动态"
    return "\n".join(
        [
            f"[Tibo Radar · {kind}]",
            post.text,
            "",
            f"发布时间: {post.created_at.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}",
            f"原帖: {post.url}",
            "信源: TwitterAPI.io（非 X 官方 API）",
        ]
    )


class _StateFileLock:
    def __init__(self, path, blocking=False):
        self.path = path
        self.blocking = blocking
        self.file = None
        self.acquired = False

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.file = open(self.path, "a+")
        if fcntl is None:
            self.acquired = True
            return self
        try:
            mode = fcntl.LOCK_EX if self.blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
            fcntl.flock(self.file.fileno(), mode)
            self.acquired = True
        except BlockingIOError:
            self.acquired = False
        return self

    def __exit__(self, *_):
        if self.file is not None:
            if self.acquired and fcntl is not None:
                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
            self.file.close()


class TiboRadar:
    def __init__(
        self,
        source,
        state_store: TiboRadarStateStore,
        sender: Callable,
        group_id: int,
        bootstrap_send: bool = False,
    ):
        self.source = source
        self.state_store = state_store
        self.sender = sender
        self.group_id = int(group_id)
        self.bootstrap_send = bootstrap_send

    def check_and_push(self, now: datetime = None) -> TiboRadarResult:
        now = now or datetime.now(timezone.utc)
        with self.state_store.try_lock() as lock:
            if not lock.acquired:
                return TiboRadarResult()
            return self._check_and_push_locked(now)

    def _check_and_push_locked(self, now: datetime) -> TiboRadarResult:
        pending_result = self._push_posts_locked(
            self.state_store.pending_posts(),
            now,
            seed_if_uninitialized=False,
            advance_checked=False,
        )
        if pending_result.failed_ids:
            return pending_result
        posts = self.source.fetch_since(self.state_store.query_since(now), now)
        search_result = self._push_posts_locked(
            posts, now, seed_if_uninitialized=True, advance_checked=True
        )
        return TiboRadarResult(
            seeded_ids=search_result.seeded_ids,
            pushed_ids=pending_result.pushed_ids + search_result.pushed_ids,
            failed_ids=search_result.failed_ids,
        )

    def push_posts(self, posts: List[TiboPost], now: datetime = None) -> TiboRadarResult:
        now = now or datetime.now(timezone.utc)
        with self.state_store.try_lock(blocking=True) as lock:
            if not lock.acquired:
                return TiboRadarResult()
            self.state_store.enqueue_pending(posts, now)
            return self._push_posts_locked(
                self.state_store.pending_posts(),
                now,
                seed_if_uninitialized=False,
                advance_checked=False,
            )

    def _push_posts_locked(
        self,
        posts: List[TiboPost],
        now: datetime,
        seed_if_uninitialized: bool,
        advance_checked: bool,
    ) -> TiboRadarResult:
        posts = sorted(posts, key=lambda item: (item.created_at, item.post_id))

        if seed_if_uninitialized and not self.state_store.is_initialized() and not self.bootstrap_send:
            self.state_store.seed(posts, self.group_id, now)
            return TiboRadarResult(seeded_ids=[item.post_id for item in posts])

        pushed_ids = []
        failed_ids = []
        for item in posts:
            if self.state_store.is_completed(item.post_id, self.group_id):
                continue
            if self.sender(self.group_id, format_tibo_post(item)):
                self.state_store.mark_completed(item, self.group_id, now)
                pushed_ids.append(item.post_id)
            else:
                failed_ids.append(item.post_id)

        if advance_checked and not failed_ids:
            self.state_store.mark_checked(now)
        return TiboRadarResult(pushed_ids=pushed_ids, failed_ids=failed_ids)
