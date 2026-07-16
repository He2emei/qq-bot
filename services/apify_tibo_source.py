from typing import List

import requests

from services.tibo_radar_service import (
    TiboPost,
    TiboSourceError,
    parse_tibo_datetime,
)

SEEMUAPPS_FREE_ACTOR_ID = "seemuapps~x-tweet-scraper"
MAXIMEDUPRE_ACTOR_ID = "maximedupre~twitter-scraper"


class ApifyTiboSource:
    """Fetch a small recent timeline through an Apify Store Actor."""

    def __init__(
        self,
        api_token: str,
        handle: str,
        actor_id: str = SEEMUAPPS_FREE_ACTOR_ID,
        base_url: str = "https://api.apify.com",
        max_items: int = 25,
        run_timeout_seconds: int = 180,
        session=None,
    ):
        self.api_token = api_token
        self.handle = handle.lstrip("@")
        self.actor_id = actor_id
        self.base_url = base_url.rstrip("/")
        requested_max_items = max(1, int(max_items))
        if self.actor_id == SEEMUAPPS_FREE_ACTOR_ID:
            self.max_items = min(25, requested_max_items)
        else:
            self.max_items = requested_max_items
        self.run_timeout_seconds = int(run_timeout_seconds)
        self.session = session or requests.Session()

    def fetch_since(self, since, until) -> List[TiboPost]:
        return self.fetch_since_id(None, since, until)

    def fetch_since_id(self, since_id, since, until) -> List[TiboPost]:
        payload = self._run_actor(since_id=since_id)
        if not payload and self.actor_id == MAXIMEDUPRE_ACTOR_ID:
            return []
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

    def _run_actor(self, since_id=None):
        try:
            response = self.session.post(
                f"{self.base_url}/v2/acts/{self.actor_id}/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {self.api_token}"},
                params={
                    "timeout": self.run_timeout_seconds,
                    "maxTotalChargeUsd": 0.01,
                },
                json=self._actor_input(since_id=since_id),
                timeout=(10, self.run_timeout_seconds + 15),
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            raise TiboSourceError(f"Apify Actor 请求失败: {type(exc).__name__}") from exc

        if not isinstance(payload, list):
            raise TiboSourceError("Apify Actor 返回格式不是列表")
        if not payload and self.actor_id != MAXIMEDUPRE_ACTOR_ID:
            raise TiboSourceError("Apify Actor 未返回时间线数据")
        return payload

    def _actor_input(self, since_id=None):
        if self.actor_id == SEEMUAPPS_FREE_ACTOR_ID:
            return {
                "query": f"from:{self.handle} -filter:retweets",
                "queryType": "Latest",
                "maxItems": self.max_items,
            }
        if self.actor_id == MAXIMEDUPRE_ACTOR_ID:
            actor_input = {
                "target": "searchPosts",
                "fromUsers": [self.handle],
                "searchMode": "latest",
                "shouldIncludeOriginalPosts": True,
                "shouldIncludeQuotePosts": True,
                "shouldIncludeReplies": True,
                "shouldIncludeReposts": False,
                "maxNbItemsToScrape": self.max_items,
            }
            if since_id:
                actor_input["sinceId"] = str(since_id)
            return actor_input
        return {
            "twitterHandles": [self.handle],
            "maxItems": self.max_items,
            "includeReplies": True,
        }

    def _normalize_item(self, item, since, until):
        post_id = str(
            item.get("id")
            or item.get("id_str")
            or item.get("tweetId")
            or item.get("postId")
            or ""
        ).strip()
        text = str(
            item.get("text") or item.get("full_text") or item.get("postText") or ""
        ).strip()
        created_value = (
            item.get("createdAt")
            or item.get("created_at")
            or item.get("postDateTime")
        )
        if not post_id or not text or not created_value:
            return False, None

        author = item.get("author") if isinstance(item.get("author"), dict) else {}
        username = str(
            author.get("userName")
            or author.get("username")
            or item.get("userName")
            or item.get("username")
            or item.get("authorHandle")
            or self.handle
        ).lstrip("@")
        if username.lower() != self.handle.lower():
            return True, None
        if (
            item.get("isRetweet")
            or item.get("retweeted_tweet")
            or item.get("retweetedTweet")
            or text.upper().startswith("RT @")
        ):
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
                or item.get("postUrl")
                or f"https://x.com/{self.handle}/status/{post_id}"
            ),
            is_reply=bool(
                item.get("isReply")
                or item.get("inReplyToId")
                or item.get("in_reply_to_status_id_str")
                or item.get("replyToPostId")
            ),
            source_label="Apify Store Actor（非 X 官方 API）",
        )
