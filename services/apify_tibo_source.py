from typing import List

import requests

from services.tibo_radar_service import (
    TiboPost,
    TiboSourceError,
    parse_tibo_datetime,
)


class ApifyTiboSource:
    """Fetch a small recent timeline through an Apify Store Actor."""

    def __init__(
        self,
        api_token: str,
        handle: str,
        actor_id: str = "dami_studio~tweet-scraper",
        base_url: str = "https://api.apify.com",
        max_items: int = 4,
        run_timeout_seconds: int = 180,
        session=None,
    ):
        self.api_token = api_token
        self.handle = handle.lstrip("@")
        self.actor_id = actor_id
        self.base_url = base_url.rstrip("/")
        self.max_items = max(1, int(max_items))
        self.run_timeout_seconds = int(run_timeout_seconds)
        self.session = session or requests.Session()

    def fetch_since(self, since, until) -> List[TiboPost]:
        payload = self._run_actor()
        posts = []
        error_rows = 0
        recognized_rows = 0
        for item in payload:
            if not isinstance(item, dict):
                continue
            if item.get("error") or item.get("errorCode") or item.get("_error"):
                error_rows += 1
                continue
            recognized, post = self._normalize_item(item, since, until)
            recognized_rows += int(recognized)
            if post is not None:
                posts.append(post)

        if not recognized_rows:
            if error_rows:
                raise TiboSourceError("Apify Actor 只返回错误记录")
            raise TiboSourceError("Apify Actor 返回记录字段无法识别")
        deduplicated = {post.post_id: post for post in posts}
        return sorted(deduplicated.values(), key=lambda post: (post.created_at, post.post_id))

    def _run_actor(self):
        try:
            response = self.session.post(
                f"{self.base_url}/v2/acts/{self.actor_id}/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {self.api_token}"},
                params={"timeout": self.run_timeout_seconds},
                json={
                    "twitterHandles": [self.handle],
                    "maxItems": self.max_items,
                    "includeReplies": True,
                },
                timeout=(10, self.run_timeout_seconds + 15),
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            raise TiboSourceError(f"Apify Actor 请求失败: {type(exc).__name__}") from exc

        if not isinstance(payload, list):
            raise TiboSourceError("Apify Actor 返回格式不是列表")
        if not payload:
            raise TiboSourceError("Apify Actor 未返回时间线数据")
        return payload

    def _normalize_item(self, item, since, until):
        post_id = str(item.get("id") or item.get("id_str") or "").strip()
        text = str(item.get("text") or item.get("full_text") or "").strip()
        created_value = item.get("createdAt") or item.get("created_at")
        if not post_id or not text or not created_value:
            return False, None

        author = item.get("author") if isinstance(item.get("author"), dict) else {}
        username = str(
            author.get("userName")
            or author.get("username")
            or item.get("userName")
            or item.get("username")
            or self.handle
        ).lstrip("@")
        if username.lower() != self.handle.lower():
            return True, None
        if item.get("isRetweet") or item.get("retweeted_tweet") or item.get("retweetedTweet"):
            return True, None

        created_at = parse_tibo_datetime(str(created_value))
        if created_at < since or created_at > until:
            return True, None
        return True, TiboPost(
            post_id=post_id,
            text=text,
            created_at=created_at,
            url=str(
                item.get("url")
                or item.get("tweetUrl")
                or f"https://x.com/{self.handle}/status/{post_id}"
            ),
            is_reply=bool(
                item.get("isReply")
                or item.get("inReplyToId")
                or item.get("in_reply_to_status_id_str")
            ),
            source_label="Apify Store Actor（非 X 官方 API）",
        )
