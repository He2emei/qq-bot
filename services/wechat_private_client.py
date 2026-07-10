import hashlib
import time

import requests


class WechatPrivateApiError(RuntimeError):
    """Raised when the configured private WeChat service is unavailable or invalid."""


class WechatPrivateApiClient:
    """Signed client compatible with the reference client.py service contract."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://wxcrawl.touchturing.com",
        session=None,
        clock=time.time,
        timeout=(5, 20),
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.clock = clock
        self.timeout = timeout

    def _get_headers(self, endpoint: str, body: bytes = None) -> dict:
        timestamp = str(int(self.clock()))
        body_md5 = hashlib.md5(body).hexdigest() if body else ""
        message = f"{self.api_key}{endpoint}{timestamp}{body_md5}{self.api_secret}"
        return {
            "x-api-key": self.api_key,
            "x-timestamp": timestamp,
            "x-signature": hashlib.md5(message.encode()).hexdigest(),
        }

    def get_latest_articles(self, nickname: str, count: int = 5, offset: int = 0) -> dict:
        return self._get_json(
            "/api/latest_articles",
            {"nickname": nickname, "count": count, "offset": offset},
        )

    def extract_markdown(self, article_url: str) -> str:
        endpoint = "/api/extract"
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(endpoint),
                params={"url": article_url},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise WechatPrivateApiError(
                f"微信私有接口请求失败: {type(exc).__name__}"
            ) from exc

        if response.text.startswith('"'):
            try:
                markdown = response.json()
            except ValueError as exc:
                raise WechatPrivateApiError("微信私有接口 Markdown 响应无效") from exc
            if not isinstance(markdown, str):
                raise WechatPrivateApiError("微信私有接口 Markdown 响应不是文本")
            return markdown
        return response.text

    def _get_json(self, endpoint: str, params: dict) -> dict:
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(endpoint),
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise WechatPrivateApiError(
                f"微信私有接口请求失败: {type(exc).__name__}"
            ) from exc

        if not isinstance(payload, dict):
            raise WechatPrivateApiError("微信私有接口 JSON 响应不是对象")
        return payload
