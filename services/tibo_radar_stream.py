import json
import threading
from datetime import timezone

import requests

from services.tibo_radar_service import TiboPost, TiboSourceError, parse_tibo_datetime

try:
    import websockets.sync.client
except ImportError:
    websockets = None


class TwitterApiIoRuleClient:
    def __init__(self, api_key, base_url="https://api.twitterapi.io", session=None, timeout=(5, 15)):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

    def ensure_rule(self, tag, value, interval_seconds):
        headers = {"X-API-Key": self.api_key}
        try:
            response = self.session.get(
                f"{self.base_url}/oapi/tweet_filter/get_rules",
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            for rule in payload.get("rules", []):
                if rule.get("tag") == tag and rule.get("value") == value:
                    return str(rule["rule_id"])

            response = self.session.post(
                f"{self.base_url}/oapi/tweet_filter/add_rule",
                headers=headers,
                data={"tag": tag, "value": value, "interval_seconds": int(interval_seconds)},
                timeout=self.timeout,
            )
            response.raise_for_status()
            rule_id = response.json().get("rule_id")
        except (requests.RequestException, RuntimeError, ValueError, KeyError) as exc:
            raise TiboSourceError(f"TwitterAPI.io 规则配置失败: {type(exc).__name__}") from exc
        if not rule_id:
            raise TiboSourceError("TwitterAPI.io 规则响应缺少 rule_id")
        return str(rule_id)


def posts_from_stream_event(payload, handle):
    if not isinstance(payload, dict) or payload.get("event_type") != "tweet":
        return []
    normalized_handle = handle.lstrip("@").lower()
    posts = []
    for item in payload.get("tweets", []):
        author = item.get("author", {}) if isinstance(item, dict) else {}
        if str(author.get("username", "")).lower() != normalized_handle:
            continue
        post_id = str(item.get("id", "")).strip()
        text = str(item.get("text", "")).strip()
        if not post_id or not text:
            continue
        posts.append(
            TiboPost(
                post_id=post_id,
                text=text,
                created_at=parse_tibo_datetime(str(item.get("createdAt") or item.get("created_at") or "")),
                url=str(item.get("url") or f"https://x.com/{normalized_handle}/status/{post_id}"),
                is_reply=bool(item.get("isReply") or item.get("is_reply")),
            )
        )
    return posts


class TwitterApiIoStreamWorker:
    def __init__(
        self,
        radar,
        api_key,
        handle,
        base_url,
        websocket_url,
        rule_tag,
        rule_interval_seconds=5,
        reconnect_seconds=90,
    ):
        self.radar = radar
        self.api_key = api_key
        self.handle = handle
        self.websocket_url = websocket_url
        self.rule_tag = rule_tag
        self.rule_value = f"from:{handle} -filter:nativeretweets"
        self.rule_interval_seconds = rule_interval_seconds
        self.reconnect_seconds = reconnect_seconds
        self.rule_client = TwitterApiIoRuleClient(api_key, base_url)
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(
            target=self.run_forever, name="tibo-radar-stream", daemon=True
        )
        self.thread.start()
        return self.thread

    def stop(self):
        self.stop_event.set()

    def join(self, timeout=None):
        if self.thread is not None:
            self.thread.join(timeout)

    def run_forever(self):
        if websockets is None:
            print("Tibo Radar WebSocket 不可用：缺少 websockets.sync.client", flush=True)
            return
        while not self.stop_event.is_set():
            with self.radar.state_store.try_stream_lock() as stream_lock:
                if not stream_lock.acquired:
                    self.stop_event.wait(self.reconnect_seconds)
                    continue
                while not self.stop_event.is_set():
                    try:
                        try:
                            self.radar.check_and_push()
                        except Exception as exc:
                            print(
                                f"Tibo Radar 建连前补漏失败: {type(exc).__name__}",
                                flush=True,
                            )
                        self.rule_client.ensure_rule(
                            self.rule_tag, self.rule_value, self.rule_interval_seconds
                        )
                        with websockets.sync.client.connect(
                            self.websocket_url,
                            additional_headers={"x-api-key": self.api_key},
                            open_timeout=15,
                            close_timeout=5,
                        ) as websocket:
                            print("Tibo Radar 实时流已连接", flush=True)
                            while not self.stop_event.is_set():
                                try:
                                    raw_message = websocket.recv(timeout=60)
                                except TimeoutError:
                                    continue
                                payload = json.loads(raw_message)
                                posts = posts_from_stream_event(payload, self.handle)
                                if posts:
                                    self.radar.push_posts(posts)
                    except Exception as exc:
                        print(f"Tibo Radar 实时流断开: {type(exc).__name__}", flush=True)
                    self.stop_event.wait(self.reconnect_seconds)
