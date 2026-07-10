# 微信 AI 早报自动推送恢复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用可回退的微信私有接口与哔哩哔哩发现源替代失效 RSS，同时继续解析微信公众号正文并可靠推送到 QQ 群。

**Architecture:** 发现层返回统一的 `DailyIssueCandidate`，哔哩哔哩适配器先恢复生产链路，私有微信适配器随后成为首选来源并在失败时回退哔哩哔哩。正文层严格校验微信域名、公众号与日期后规范化为向后兼容的 `RssEntry`；推送层按群记录成功状态，只有普通消息和合并转发都成功才完成该群去重。

**Tech Stack:** Python 3、`requests`、BeautifulSoup 4、APScheduler、`unittest`/`unittest.mock`、NapCat WebSocket/HTTP。

## Global Constraints

- 保留 `#rssdaily`、`#rsskw`、`RssEntry`、现有群组配置和普通消息/合并转发格式。
- 最终来源顺序默认为 `wechat_private,bilibili`；缺少微信 API 密钥时自动只使用 `bilibili`。
- B 站账号必须同时匹配 MID `285286947`、名称 `橘鸦Juya` 和 `【AI 早报 YYYY-MM-DD】` 标题。
- 微信正文只接受 HTTPS `mp.weixin.qq.com`、公众号 `橘鸦Juya`，候选日期必须与文章标题一致。
- B 站只使用进程内匿名 Cookie；不读取、记录或持久化登录 Cookie。
- 微信 API Key、API Secret、签名、完整鉴权头和运行时状态不得进入版本库或日志。
- 默认轮询间隔 300 秒；B 站 412 只刷新匿名会话并重试一次。
- 标准测试不依赖外网；实时验证显式运行且不发送 QQ 消息。
- 每次提交只暂存任务列出的文件，保留工作树中的用户无关改动。

## File Map

- Create `services/ai_daily_source.py`: 候选模型、来源协议、回退和同日视频补全。
- Create `services/bilibili_daily_source.py`: B 站匿名会话、搜索、链接提取和 412 恢复。
- Create `services/wechat_article_service.py`: 微信 HTML 获取、校验、Markdown 回退和规范化。
- Create `services/wechat_private_client.py`: `client.py` 签名、最新文章和提取请求。
- Create `services/wechat_daily_source.py`: 私有接口响应到候选模型的适配。
- Create `services/ai_daily_factory.py`: 按配置组装来源和正文服务。
- Modify `services/rss_service.py`: 给 `RssEntry` 增加兼容来源元数据。
- Modify `services/rss_filter_service.py`: 提取微信纯文本来源 URL。
- Modify `services/rss_display_service.py`: 优先显示结构化视频 URL。
- Modify `services/rss_push_service.py`: 新运行时、空正文保护、按群状态和原子写入。
- Modify `services/rss_scheduler.py`, `handlers/rss_handler.py`, `utils/api_utils.py`: 统一新流程和发送结果。
- Modify `config.py`; create `.env.example`, smoke script and部署文档。

---

### Task 1: 统一候选模型与 B 站发现源

**Files:**
- Create: `services/ai_daily_source.py`
- Create: `services/bilibili_daily_source.py`
- Create: `tests/unit/test_bilibili_daily_source.py`

**Interfaces:**
- Produces: `DailyIssueCandidate`, `DailySourceError`, `DailyIssueDiscovery.discover_latest()`, `BilibiliDailySource.discover_latest()`, `find_by_date(issue_date)`。
- Consumes: 注入的 `requests.Session`；不依赖后续任务。

- [ ] **Step 1: 写候选发现、最新一期缺链、412 恢复和来源回退的失败测试**

```python
# tests/unit/test_bilibili_daily_source.py
import unittest
from datetime import date, datetime
from unittest.mock import Mock

from services.ai_daily_source import DailyIssueCandidate, DailyIssueDiscovery, DailySourceError
from services.bilibili_daily_source import BilibiliDailySource


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def video(title="今日标题【AI 早报 2026-07-10】", description="相关链接：https://mp.weixin.qq.com/s/article-id"):
    return {
        "mid": 285286947, "author": "橘鸦Juya", "title": title,
        "description": description, "bvid": "BV1YiNj6nE7n", "pubdate": 1783649249,
    }


class BilibiliDailySourceTest(unittest.TestCase):
    def make_source(self, responses):
        session = Mock()
        session.cookies = Mock()
        session.get.side_effect = responses
        return BilibiliDailySource(285286947, "橘鸦Juya", "橘鸦Juya", session=session), session

    def test_discovers_latest_matching_video_and_wechat_link(self):
        payload = {"code": 0, "data": {"result": [video()]}}
        source, session = self.make_source([FakeResponse(), FakeResponse(payload=payload)])
        result = source.discover_latest()
        self.assertEqual(result.issue_date, date(2026, 7, 10))
        self.assertEqual(result.article_url, "https://mp.weixin.qq.com/s/article-id")
        self.assertEqual(result.video_url, "https://www.bilibili.com/video/BV1YiNj6nE7n/")
        self.assertEqual(session.get.call_count, 2)

    def test_latest_without_link_never_falls_back_to_yesterday(self):
        today = video(description="")
        yesterday = video("昨日【AI 早报 2026-07-09】", "https://mp.weixin.qq.com/s/yesterday")
        search = {"code": 0, "data": {"result": [today, yesterday]}}
        detail = {"code": 0, "data": {"desc": ""}}
        source, _ = self.make_source([FakeResponse(), FakeResponse(payload=search), FakeResponse(payload=detail)])
        with self.assertRaisesRegex(DailySourceError, "缺少微信链接"):
            source.discover_latest()

    def test_412_rebuilds_session_once(self):
        payload = {"code": 0, "data": {"result": [video()]}}
        source, session = self.make_source([
            FakeResponse(), FakeResponse(status_code=412),
            FakeResponse(), FakeResponse(payload=payload),
        ])
        self.assertEqual(source.discover_latest().source_id, "BV1YiNj6nE7n")
        self.assertEqual(session.get.call_count, 4)

    def test_coordinator_falls_back_and_enriches_video(self):
        first = Mock()
        first.discover_latest.side_effect = DailySourceError("private unavailable")
        candidate = DailyIssueCandidate(
            title="t", article_url="https://mp.weixin.qq.com/s/x",
            published_at=datetime.fromisoformat("2026-07-10T09:00:00+08:00"),
            issue_date=date(2026, 7, 10), source_id="x", discovered_by="fallback",
        )
        second = Mock()
        second.discover_latest.return_value = candidate
        resolver = Mock()
        resolver.find_by_date.return_value = "https://www.bilibili.com/video/BV123/"
        result = DailyIssueDiscovery([first, second], resolver).discover_latest()
        self.assertEqual(result.video_url, "https://www.bilibili.com/video/BV123/")
```

- [ ] **Step 2: 运行测试并验证失败**

Run: `python -m unittest tests.unit.test_bilibili_daily_source -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'services.ai_daily_source'`。

- [ ] **Step 3: 实现共享模型与回退协调器**

```python
# services/ai_daily_source.py
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Iterable, Protocol


@dataclass(frozen=True)
class DailyIssueCandidate:
    title: str
    article_url: str
    published_at: datetime
    issue_date: date
    source_id: str
    video_url: str = ""
    discovered_by: str = ""


class DailySourceError(RuntimeError):
    pass


class DailySource(Protocol):
    def discover_latest(self) -> DailyIssueCandidate: ...


class VideoResolver(Protocol):
    def find_by_date(self, issue_date: date) -> str: ...


class DailyIssueDiscovery:
    def __init__(self, sources: Iterable[DailySource], video_resolver: VideoResolver = None):
        self.sources = list(sources)
        self.video_resolver = video_resolver

    def discover_latest(self) -> DailyIssueCandidate:
        errors = []
        for source in self.sources:
            try:
                candidate = source.discover_latest()
            except DailySourceError as exc:
                errors.append(f"{type(source).__name__}: {exc}")
                continue
            if not candidate.video_url and self.video_resolver:
                try:
                    video_url = self.video_resolver.find_by_date(candidate.issue_date)
                except DailySourceError as exc:
                    print(f"AI早报视频补全失败: {exc}", flush=True)
                else:
                    if video_url:
                        candidate = replace(candidate, video_url=video_url)
            return candidate
        raise DailySourceError("; ".join(errors) or "未配置可用的AI早报来源")
```

- [ ] **Step 4: 实现 B 站匿名搜索适配器**

```python
# services/bilibili_daily_source.py
import re
from datetime import date, datetime
from html import unescape
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from services.ai_daily_source import DailyIssueCandidate, DailySourceError

HOME_URL = "https://www.bilibili.com/"
SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"
VIEW_URL = "https://api.bilibili.com/x/web-interface/view"
TITLE_DATE_RE = re.compile(r"【AI\s*早报\s*(\d{4}-\d{2}-\d{2})】")
WECHAT_URL_RE = re.compile(r"https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+")


class BilibiliDailySource:
    def __init__(self, uploader_mid, uploader_name, keyword, session=None, timeout=(5, 15)):
        self.uploader_mid = int(uploader_mid)
        self.uploader_name = uploader_name
        self.keyword = keyword
        self.session = session or requests.Session()
        self.timeout = timeout
        self._bootstrapped = False
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://search.bilibili.com/all?keyword={keyword}",
        })

    def discover_latest(self):
        videos = self._matching_videos()
        if not videos:
            raise DailySourceError("未找到目标账号的AI早报投稿")
        item = videos[0]
        article_url = self._article_url(item)
        if not article_url:
            raise DailySourceError(f"最新一期 {item.get('bvid', '')} 缺少微信链接")
        issue_date = self._issue_date(item["title"])
        return DailyIssueCandidate(
            title=item["title"], article_url=article_url,
            published_at=datetime.fromtimestamp(int(item["pubdate"]), ZoneInfo("Asia/Shanghai")),
            issue_date=issue_date, source_id=item["bvid"],
            video_url=self._video_url(item["bvid"]), discovered_by="bilibili",
        )

    def find_by_date(self, issue_date):
        for item in self._matching_videos():
            if self._issue_date(item["title"]) == issue_date:
                return self._video_url(item["bvid"])
        return ""

    def _matching_videos(self):
        data = self._request_data(SEARCH_URL, {
            "search_type": "video", "keyword": self.keyword, "order": "pubdate", "page": 1,
        })
        matches = []
        for raw in data.get("result", []):
            item = dict(raw)
            item["title"] = BeautifulSoup(unescape(item.get("title", "")), "html.parser").get_text(" ", strip=True)
            if (item.get("mid") == self.uploader_mid
                    and item.get("author") == self.uploader_name
                    and TITLE_DATE_RE.search(item["title"])):
                matches.append(item)
        return sorted(matches, key=lambda item: int(item.get("pubdate", 0)), reverse=True)

    def _article_url(self, item):
        match = WECHAT_URL_RE.search(item.get("description", ""))
        if match:
            return match.group(0)
        data = self._request_data(VIEW_URL, {"bvid": item.get("bvid", "")})
        match = WECHAT_URL_RE.search(data.get("desc", ""))
        return match.group(0) if match else ""

    def _request_data(self, url, params):
        for attempt in range(2):
            self._bootstrap(reset=attempt == 1)
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 412 and attempt == 0:
                self._bootstrapped = False
                continue
            try:
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError, RuntimeError) as exc:
                raise DailySourceError(f"B站请求失败: {exc}") from exc
            if payload.get("code") != 0 or not isinstance(payload.get("data"), dict):
                raise DailySourceError(f"B站响应异常: code={payload.get('code')}")
            return payload["data"]
        raise DailySourceError("B站风控校验失败: HTTP 412")

    def _bootstrap(self, reset=False):
        if reset:
            self.session.cookies.clear()
            self._bootstrapped = False
        if self._bootstrapped:
            return
        try:
            response = self.session.get(HOME_URL, timeout=self.timeout)
            response.raise_for_status()
        except (requests.RequestException, RuntimeError) as exc:
            raise DailySourceError(f"B站匿名会话建立失败: {exc}") from exc
        self._bootstrapped = True

    @staticmethod
    def _issue_date(title):
        match = TITLE_DATE_RE.search(title)
        if not match:
            raise DailySourceError("投稿标题缺少AI早报日期")
        return date.fromisoformat(match.group(1))

    @staticmethod
    def _video_url(bvid):
        return f"https://www.bilibili.com/video/{bvid}/"
```

- [ ] **Step 5: 运行测试并提交**

Run: `python -m unittest tests.unit.test_bilibili_daily_source -v`

Expected: 4 tests, all PASS。

```powershell
git add -- services/ai_daily_source.py services/bilibili_daily_source.py tests/unit/test_bilibili_daily_source.py
git commit -m "feat: add bilibili AI daily discovery"
```

---

### Task 2: 获取并严格校验微信 HTML 正文

**Files:**
- Modify: `services/rss_service.py:10-23`
- Create: `services/wechat_article_service.py`
- Create: `tests/unit/test_wechat_article_service.py`
- Modify: `tests/unit/test_rss_service.py`

**Interfaces:**
- Consumes: `DailyIssueCandidate` 和现有 `html_to_text()`。
- Produces: `WechatArticleService.fetch(candidate) -> RssEntry`，以及兼容默认字段 `video_url`、`discovery_source`。

- [ ] **Step 1: 写有效正文与域名、公众号、日期、正文缺失校验的失败测试**

```python
# tests/unit/test_wechat_article_service.py
import unittest
from datetime import date, datetime
from unittest.mock import Mock

from services.ai_daily_source import DailyIssueCandidate
from services.wechat_article_service import WechatArticleError, WechatArticleService

HTML = """<h1 id="activity-name">今日【AI 早报 2026-07-10】</h1>
<span id="js_name">橘鸦Juya</span>
<div id="js_content"><h3>要闻</h3><ul><li>新闻 #1</li></ul>
<h2>新闻标题 #1</h2><p>正文 https://example.com/source</p></div>"""


def candidate(url="https://mp.weixin.qq.com/s/article-id"):
    return DailyIssueCandidate(
        title="今日【AI 早报 2026-07-10】", article_url=url,
        published_at=datetime.fromisoformat("2026-07-10T09:00:00+08:00"),
        issue_date=date(2026, 7, 10), source_id="source",
        video_url="https://www.bilibili.com/video/BV1/", discovered_by="bilibili",
    )


class WechatArticleServiceTest(unittest.TestCase):
    def service(self, html=HTML):
        response = Mock(text=html, url="https://mp.weixin.qq.com/s/article-id?nwr_flag=1")
        response.raise_for_status.return_value = None
        session = Mock()
        session.get.return_value = response
        return WechatArticleService("橘鸦Juya", session=session), session

    def test_fetches_valid_article_as_rss_entry(self):
        service, _ = self.service()
        entry = service.fetch(candidate())
        self.assertEqual(entry.title, "2026-07-10")
        self.assertEqual(entry.link, "https://mp.weixin.qq.com/s/article-id")
        self.assertEqual(entry.entry_id, entry.link)
        self.assertEqual(entry.video_url, "https://www.bilibili.com/video/BV1/")
        self.assertIn("新闻标题", entry.content_text)

    def test_rejects_non_wechat_url_without_network(self):
        service, session = self.service()
        with self.assertRaisesRegex(WechatArticleError, "微信文章域名"):
            service.fetch(candidate("https://example.com/article"))
        session.get.assert_not_called()

    def test_rejects_wrong_account_date_and_missing_content(self):
        service, _ = self.service(HTML.replace("橘鸦Juya", "其他账号"))
        with self.assertRaisesRegex(WechatArticleError, "公众号不匹配"):
            service.fetch(candidate())
        service, _ = self.service(HTML.replace("2026-07-10", "2026-07-09"))
        with self.assertRaisesRegex(WechatArticleError, "日期不匹配"):
            service.fetch(candidate())
        service, _ = self.service(HTML.replace('id="js_content"', 'id="missing"'))
        with self.assertRaisesRegex(WechatArticleError, "正文"):
            service.fetch(candidate())
```

在 `test_rss_service.py` 正常化断言末尾添加：

```python
self.assertEqual(entries[0].video_url, "")
self.assertEqual(entries[0].discovery_source, "rss")
```

- [ ] **Step 2: 运行测试并验证失败**

Run: `python -m unittest tests.unit.test_wechat_article_service tests.unit.test_rss_service -v`

Expected: FAIL，新增模块或 `RssEntry` 字段不存在。

- [ ] **Step 3: 扩展 `RssEntry` 并实现正文服务**

```python
# services/rss_service.py: RssEntry
@dataclass(frozen=True)
class RssEntry:
    title: str
    link: str
    published: str
    summary: str
    content_html: str
    content_text: str
    entry_id: str
    video_url: str = ""
    discovery_source: str = "rss"
```

```python
# services/wechat_article_service.py
import re
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

from services.rss_service import RssEntry, html_to_text

DATE_RE = re.compile(r"AI\s*早报\s*(\d{4}-\d{2}-\d{2})")
CANONICAL_RE = re.compile(r"^https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+")


class WechatArticleError(RuntimeError):
    pass


class WechatArticleTransportError(WechatArticleError):
    pass


class WechatArticleService:
    def __init__(self, account_nickname, session=None, timeout=(5, 20)):
        self.account_nickname = account_nickname
        self.session = session or requests.Session()
        self.timeout = timeout
        self.headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 13) Mobile MicroMessenger/8.0.49"}

    def fetch(self, candidate):
        canonical = self._canonical_url(candidate.article_url)
        try:
            response = self.session.get(canonical, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise WechatArticleTransportError(f"微信文章获取失败: {exc}") from exc
        self._canonical_url(response.url)
        soup = BeautifulSoup(response.text, "html.parser")
        title_node = soup.select_one("#activity-name, .rich_media_title")
        account_node = soup.select_one("#js_name, .rich_media_meta_nickname")
        content_node = soup.select_one("#js_content")
        if not title_node or not content_node:
            raise WechatArticleTransportError("微信文章正文或标题缺失")
        account = account_node.get_text(" ", strip=True) if account_node else ""
        if account != self.account_nickname:
            raise WechatArticleError(f"微信公众号不匹配: {account}")
        article_title = title_node.get_text(" ", strip=True)
        match = DATE_RE.search(article_title)
        if not match or match.group(1) != candidate.issue_date.isoformat():
            raise WechatArticleError("微信文章日期不匹配")
        content_html = str(content_node)
        return RssEntry(
            title=candidate.issue_date.isoformat(), link=canonical,
            published=candidate.published_at.isoformat(), summary=article_title,
            content_html=content_html, content_text=html_to_text(content_html),
            entry_id=canonical, video_url=candidate.video_url,
            discovery_source=candidate.discovered_by,
        )

    @staticmethod
    def _canonical_url(url):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "mp.weixin.qq.com":
            raise WechatArticleError("只允许 HTTPS 微信文章域名 mp.weixin.qq.com")
        match = CANONICAL_RE.match(url)
        if not match:
            raise WechatArticleError("微信文章链接格式无效")
        return match.group(0)
```

- [ ] **Step 4: 运行测试并提交**

Run: `python -m unittest tests.unit.test_wechat_article_service tests.unit.test_rss_service -v`

Expected: all PASS。

```powershell
git add -- services/rss_service.py services/wechat_article_service.py tests/unit/test_wechat_article_service.py tests/unit/test_rss_service.py
git commit -m "feat: parse validated WeChat daily articles"
```

---

### Task 3: 解析微信纯文本来源链接并显示结构化视频链接

**Files:**
- Modify: `services/rss_filter_service.py:111-177`
- Modify: `services/rss_display_service.py:39-63`
- Modify: `tests/unit/test_rss_filter_service.py`
- Modify: `tests/unit/test_rss_display_service.py`

**Interfaces:**
- Consumes: `RssEntry.content_html`、`RssEntry.video_url`。
- Produces: `RssNewsItem.url` 可从标题锚点或正文纯文本 URL 获得。

- [ ] **Step 1: 添加纯文本 URL、微信内部链接排除和视频 URL 优先级的失败测试**

```python
# tests/unit/test_rss_filter_service.py
def test_extract_news_items_uses_plain_text_source_url(self):
    entry = RssEntry(
        title="2026-07-10", link="https://mp.weixin.qq.com/s/x", published="",
        summary="", entry_id="x", content_text="",
        content_html="""<h3>要闻</h3><ul><li>标题 #1</li></ul>
        <h2>标题 #1</h2><p>https://mp.weixin.qq.com/mp/readtemplate?t=internal</p>
        <p>https://example.com/source。</p>""",
    )
    result = classify_rss_entry(entry, keywords=[])
    self.assertEqual(result.all_items[0].url, "https://example.com/source")
```

在 `test_rss_display_service.py` 的样本 `RssEntry` 添加：

```python
video_url="https://www.bilibili.com/video/BV_STRUCTURED/",
```

并断言：

```python
self.assertIn("哔哩哔哩视频版：https://www.bilibili.com/video/BV_STRUCTURED/", source_text)
```

- [ ] **Step 2: 运行测试并验证旧解析逻辑失败**

Run: `python -m unittest tests.unit.test_rss_filter_service tests.unit.test_rss_display_service -v`

Expected: FAIL，纯文本 URL 为空且展示仍使用 HTML 内旧链接。

- [ ] **Step 3: 实现 URL 选择与视频优先级**

在 `rss_filter_service.py` 添加 `from urllib.parse import urlsplit`，并把新闻 URL 赋值改为：

```python
section_html = _collect_section_html(heading)
url = _extract_source_url(title_link, section_html)
content_text = html_to_text(section_html)
```

添加：

```python
SOURCE_URL_RE = re.compile(r"https?://[^\s<>\"']+")
INTERNAL_SOURCE_HOSTS = {"mp.weixin.qq.com", "mmbiz.qpic.cn"}


def _extract_source_url(title_link, section_html):
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
```

把 `rss_display_service._format_source_info()` 的视频行改为：

```python
bilibili_url = result.entry.video_url or _extract_bilibili_url(result.entry.content_html)
```

- [ ] **Step 4: 运行测试并提交**

Run: `python -m unittest tests.unit.test_rss_filter_service tests.unit.test_rss_display_service -v`

Expected: all PASS。

```powershell
git add -- services/rss_filter_service.py services/rss_display_service.py tests/unit/test_rss_filter_service.py tests/unit/test_rss_display_service.py
git commit -m "feat: extract WeChat news source links"
```

---

### Task 4: 组装第一阶段 B 站运行时

**Files:**
- Create: `services/ai_daily_factory.py`
- Modify: `config.py:82-92`
- Create: `tests/unit/test_ai_daily_factory.py`

**Interfaces:**
- Consumes: Tasks 1-2 的 B 站来源、协调器和正文服务。
- Produces: `AiDailyRuntime`, `build_ai_daily_runtime()`；Task 5 只依赖该运行时。

- [ ] **Step 1: 写只启用 B 站时的失败测试**

```python
# tests/unit/test_ai_daily_factory.py
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.ai_daily_factory import build_ai_daily_runtime


class AiDailyFactoryTest(unittest.TestCase):
    def test_builds_bilibili_runtime_without_private_credentials(self):
        fake = SimpleNamespace(
            AI_DAILY_SOURCE_ORDER=["bilibili"],
            BILIBILI_UPLOADER_MID=285286947,
            BILIBILI_UPLOADER_NAME="橘鸦Juya",
            BILIBILI_SEARCH_KEYWORD="橘鸦Juya",
            WECHAT_ACCOUNT_NICKNAME="橘鸦Juya",
            WECHAT_API_BASE_URL="https://wxcrawl.touchturing.com",
            WECHAT_API_KEY="", WECHAT_API_SECRET="",
        )
        with patch("services.ai_daily_factory.config", fake):
            runtime = build_ai_daily_runtime()
        self.assertEqual([type(source).__name__ for source in runtime.discovery.sources], ["BilibiliDailySource"])
        self.assertEqual(runtime.article_service.account_nickname, "橘鸦Juya")
```

- [ ] **Step 2: 运行测试并验证工厂不存在**

Run: `python -m unittest tests.unit.test_ai_daily_factory -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'services.ai_daily_factory'`。

- [ ] **Step 3: 添加第一阶段配置**

在 `config.py` 的 RSS 配置段使用：

```python
RSS_SOURCE_NAME = "橘鸦AI早报"
RSS_SOURCE_URL = "https://mp.weixin.qq.com/"
RSS_POLL_INTERVAL_SECONDS = int(os.getenv("RSS_POLL_INTERVAL_SECONDS", "300"))
AI_DAILY_SOURCE_ORDER = [
    item.strip() for item in os.getenv("AI_DAILY_SOURCE_ORDER", "bilibili").split(",") if item.strip()
]
BILIBILI_UPLOADER_MID = int(os.getenv("BILIBILI_UPLOADER_MID", "285286947"))
BILIBILI_UPLOADER_NAME = os.getenv("BILIBILI_UPLOADER_NAME", "橘鸦Juya")
BILIBILI_SEARCH_KEYWORD = os.getenv("BILIBILI_SEARCH_KEYWORD", "橘鸦Juya")
WECHAT_ACCOUNT_NICKNAME = os.getenv("WECHAT_ACCOUNT_NICKNAME", "橘鸦Juya")
WECHAT_API_BASE_URL = os.getenv("WECHAT_API_BASE_URL", "https://wxcrawl.touchturing.com")
WECHAT_API_KEY = os.getenv("WECHAT_API_KEY", "")
WECHAT_API_SECRET = os.getenv("WECHAT_API_SECRET", "")
```

- [ ] **Step 4: 实现运行时工厂**

```python
# services/ai_daily_factory.py
from dataclasses import dataclass

import config
from services.ai_daily_source import DailyIssueDiscovery
from services.bilibili_daily_source import BilibiliDailySource
from services.wechat_article_service import WechatArticleService


@dataclass(frozen=True)
class AiDailyRuntime:
    discovery: DailyIssueDiscovery
    article_service: WechatArticleService


def build_ai_daily_runtime():
    bilibili = BilibiliDailySource(
        config.BILIBILI_UPLOADER_MID,
        config.BILIBILI_UPLOADER_NAME,
        config.BILIBILI_SEARCH_KEYWORD,
    )
    sources = []
    for source_name in config.AI_DAILY_SOURCE_ORDER:
        if source_name == "bilibili":
            sources.append(bilibili)
        elif source_name == "wechat_private":
            if config.WECHAT_API_KEY and config.WECHAT_API_SECRET:
                raise RuntimeError("wechat_private 尚未在 Task 6 接入")
        else:
            raise ValueError(f"未知AI早报来源: {source_name}")
    return AiDailyRuntime(
        discovery=DailyIssueDiscovery(sources, video_resolver=bilibili),
        article_service=WechatArticleService(config.WECHAT_ACCOUNT_NICKNAME),
    )
```

- [ ] **Step 5: 运行第一阶段工厂测试并提交**

Run: `python -m unittest tests.unit.test_ai_daily_factory tests.unit.test_bilibili_daily_source tests.unit.test_wechat_article_service -v`

Expected: all PASS。

```powershell
git add -- config.py services/ai_daily_factory.py tests/unit/test_ai_daily_factory.py
git commit -m "feat: configure bilibili AI daily runtime"
```

---

### Task 5: 将自动与手动推送切换到新运行时并实现按群状态

**Files:**
- Modify: `services/rss_push_service.py:1-82`
- Modify: `services/rss_scheduler.py:1-54`
- Modify: `handlers/rss_handler.py:1-23`
- Modify: `utils/api_utils.py:70-97`
- Modify: `tests/unit/test_rss_push_service.py`
- Create: `tests/unit/test_api_utils_rss.py`
- Create: `tests/unit/test_rss_handler.py`

**Interfaces:**
- Consumes: `AiDailyRuntime.discovery`、`article_service` 和现有格式化器。
- Produces: `check_and_push_latest_rss(force=False, group_ids=None, runtime=None, state_store=None)`、按群原子状态、可判定 QQ 结果。

- [ ] **Step 1: 写旧状态迁移、部分群重试、空正文保护和 HTTP 返回值失败测试**

在 `test_rss_push_service.py` 添加 imports `json`, `replace`, `Mock`，删除依赖 `fetch_rss_entries`、`get_last_entry_id()`、`mark_pushed()` 的三个旧流程测试，并把 `_sample_entry()` 的 `content_html` 改成可由分类器识别的最小一期：

```python
content_html="""<h3>要闻</h3><ul><li>测试新闻 #1</li></ul>
<h2>测试新闻 #1</h2><p>https://example.com/source</p>""",
```

再添加：

```python
def test_legacy_state_migrates_without_resend(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "rss_state.json"
        path.write_text('{"last_entry_id":"entry-1"}', encoding="utf-8")
        store = RssPushStateStore(str(path))
        self.assertEqual(store.completed_groups("entry-1", [11, 22]), {11, 22})
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(set(data["groups"]), {"11", "22"})

def test_corrupt_state_recovers_as_empty(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "rss_state.json"
        path.write_text("{broken", encoding="utf-8")
        store = RssPushStateStore(str(path))
        self.assertEqual(store.completed_groups("entry-1", [11]), set())

def test_partial_failure_retries_only_failed_group(self):
    entry = _sample_entry("entry-1")
    runtime = Mock()
    runtime.discovery.discover_latest.return_value = Mock()
    runtime.article_service.fetch.return_value = entry
    with tempfile.TemporaryDirectory() as temp_dir:
        store = RssPushStateStore(str(Path(temp_dir) / "rss_state.json"))
        with patch.object(rss_push_service, "send_group_message", return_value={"ok": True}), \
             patch.object(rss_push_service, "send_group_forward_message", side_effect=[{"ok": True}, None]):
            first = check_and_push_latest_rss(group_ids=[11, 22], runtime=runtime, state_store=store)
        self.assertEqual(first.group_ids, [11])
        self.assertEqual(first.failed_group_ids, [22])
        with patch.object(rss_push_service, "send_group_message", return_value={"ok": True}) as plain, \
             patch.object(rss_push_service, "send_group_forward_message", return_value={"ok": True}):
            second = check_and_push_latest_rss(group_ids=[11, 22], runtime=runtime, state_store=store)
        plain.assert_called_once_with(22, unittest.mock.ANY)
        self.assertEqual(second.group_ids, [22])

def test_zero_news_never_sends(self):
    entry = replace(_sample_entry("empty"), content_html="<h1>empty</h1>")
    with patch.object(rss_push_service, "send_group_message") as send:
        with self.assertRaisesRegex(RssPushError, "没有解析到新闻"):
            push_rss_entry(entry, [11], state_store=Mock())
    send.assert_not_called()
```

```python
# tests/unit/test_api_utils_rss.py
import unittest
from unittest.mock import Mock, patch
from utils.api_utils import send_group_message


class ApiUtilsRssTest(unittest.TestCase):
    @patch("utils.api_utils._napcat_ws_request", return_value=None)
    @patch("utils.api_utils.requests.get")
    def test_http_success_returns_non_empty_result(self, request_get, _ws):
        response = Mock(status_code=200, text="ok")
        response.json.side_effect = ValueError()
        request_get.return_value = response
        self.assertEqual(send_group_message(11, "hello"), {"raw": "ok"})
```

```python
# tests/unit/test_rss_handler.py
import unittest
from unittest.mock import patch
from handlers.rss_handler import handle_rss_daily_command


class RssHandlerTest(unittest.TestCase):
    @patch("handlers.rss_handler.check_and_push_latest_rss")
    def test_manual_command_uses_force_pipeline(self, check):
        handle_rss_daily_command({"group_id": 123, "message": "#rssdaily"})
        check.assert_called_once_with(force=True, group_ids=[123])
```

- [ ] **Step 2: 运行测试并验证旧推送逻辑失败**

Run: `python -m unittest tests.unit.test_rss_push_service tests.unit.test_api_utils_rss tests.unit.test_rss_handler -v`

Expected: FAIL，缺少 `completed_groups`、`failed_group_ids`，HTTP 成功返回 `None`，handler 仍取 RSS。

- [ ] **Step 3: 实现按群状态、原子写入和新推送编排**

`rss_push_service.py` 保留现有 imports 和格式化调用，但用以下接口替换单 ID 状态：

```python
from dataclasses import dataclass, field
from tempfile import NamedTemporaryFile
from typing import Dict, List, Set, Tuple
from services.ai_daily_factory import build_ai_daily_runtime


class RssPushError(RuntimeError):
    pass


@dataclass(frozen=True)
class RssPushResult:
    pushed: bool
    entry_id: str
    title: str
    group_ids: List[int]
    failed_group_ids: List[int] = field(default_factory=list)


class RssPushStateStore:
    def __init__(self, path=None):
        self.path = path or config.DATA_PATHS["rss_state"]

    def completed_groups(self, entry_id, configured_groups):
        data = self._load_data()
        if data.get("last_entry_id") == entry_id and not data.get("entry_id"):
            data = {
                "entry_id": entry_id,
                "title": data.get("last_title", ""),
                "article_url": data.get("last_link", ""),
                "video_url": "",
                "groups": {str(group): datetime.now().isoformat(timespec="seconds") for group in configured_groups},
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
            self._save_data(data)
            return set(configured_groups)
        if data.get("entry_id") != entry_id:
            return set()
        return {int(group) for group in data.get("groups", {})}

    def mark_group_pushed(self, entry, group_id):
        data = self._load_data()
        if data.get("entry_id") != entry.entry_id:
            data = {
                "entry_id": entry.entry_id, "title": entry.title,
                "article_url": entry.link, "video_url": entry.video_url, "groups": {},
            }
        data["groups"][str(group_id)] = datetime.now().isoformat(timespec="seconds")
        data["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self._save_data(data)

    def _load_data(self):
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"AI早报状态读取失败，将从空状态恢复: {exc}", flush=True)
            return {}
        return data if isinstance(data, dict) else {}

    def _save_data(self, data):
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


def check_and_push_latest_rss(force=False, group_ids=None, runtime=None, state_store=None):
    runtime = runtime or ai_daily_runtime
    state_store = state_store or rss_push_state_store
    targets = list(group_ids if group_ids is not None else config.RSS_PUSH_GROUP_IDS)
    candidate = runtime.discovery.discover_latest()
    entry = runtime.article_service.fetch(candidate)
    completed = state_store.completed_groups(entry.entry_id, targets)
    pending = targets if force else [group for group in targets if group not in completed]
    if not pending:
        return RssPushResult(False, entry.entry_id, entry.title, [])
    sent, failed = push_rss_entry(entry, pending, state_store)
    return RssPushResult(bool(sent), entry.entry_id, entry.title, sent, failed)


def push_rss_entry(entry, group_ids, state_store=None):
    state_store = state_store or rss_push_state_store
    result = classify_rss_entry(entry)
    if not result.all_items:
        raise RssPushError("AI早报没有解析到新闻条目，拒绝推送")
    important = format_important_news_message(result)
    nodes = build_other_news_forward_nodes(result, config.RSS_FORWARD_USER_ID, config.RSS_SOURCE_NAME)
    sent, failed = [], []
    for group_id in group_ids:
        if not send_group_message(group_id, important):
            failed.append(group_id)
            continue
        if not send_group_forward_message(group_id, nodes):
            failed.append(group_id)
            continue
        state_store.mark_group_pushed(entry, group_id)
        sent.append(group_id)
    return sent, failed


rss_push_state_store = RssPushStateStore()
ai_daily_runtime = build_ai_daily_runtime()
```

- [ ] **Step 4: 修正普通消息 HTTP 成功返回值并统一 handler/scheduler**

`utils/api_utils.send_group_message()` 的 HTTP 200 分支：

```python
if response.status_code == 200:
    print(f"向群 {group_id} 发送消息成功")
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}
```

`handlers/rss_handler.py` 删除旧 RSS fetch imports，改为：

```python
from services.rss_push_service import check_and_push_latest_rss


def handle_rss_daily_command(event):
    group_id = event["group_id"]
    try:
        check_and_push_latest_rss(force=True, group_ids=[group_id])
    except Exception as exc:
        print(f"发送AI早报失败: {exc}", flush=True)
        send_group_message(group_id, f"发送AI早报失败: {exc}")
```

`rss_scheduler.check_rss_update_job()` 根据 `failed_group_ids` 输出部分失败，将运行日志中的“RSS”改为“AI早报”，保留 job id、`max_instances=1`、`coalesce=True`。

```python
def check_rss_update_job():
    try:
        print(f"[{datetime.now()}] 开始检查AI早报更新...", flush=True)
        result = check_and_push_latest_rss()
        if result.failed_group_ids:
            print(f"[{datetime.now()}] AI早报部分群推送失败: {result.failed_group_ids}", flush=True)
        if result.pushed:
            print(f"[{datetime.now()}] AI早报已推送: {result.title} -> {result.group_ids}", flush=True)
        elif not result.failed_group_ids:
            print(f"[{datetime.now()}] AI早报暂无新内容: {result.entry_id}", flush=True)
    except Exception as exc:
        print(f"[{datetime.now()}] AI早报更新检查失败: {exc}", flush=True)
```

- [ ] **Step 5: 运行相关测试并提交**

Run:

```powershell
python -m unittest tests.unit.test_rss_push_service tests.unit.test_api_utils_rss tests.unit.test_rss_handler tests.unit.test_rss_service tests.unit.test_rss_filter_service tests.unit.test_rss_display_service -v
```

Expected: all PASS；无真实 NapCat 请求。

```powershell
git add -- services/rss_push_service.py services/rss_scheduler.py handlers/rss_handler.py utils/api_utils.py tests/unit/test_rss_push_service.py tests/unit/test_api_utils_rss.py tests/unit/test_rss_handler.py
git commit -m "feat: push AI daily with per-group state"
```

---

### Task 6: 按 `client.py` 接入私有微信发现源

**Files:**
- Create: `services/wechat_private_client.py`
- Create: `services/wechat_daily_source.py`
- Create: `tests/unit/test_wechat_private_client.py`
- Create: `tests/unit/test_wechat_daily_source.py`

**Interfaces:**
- Consumes: `DailyIssueCandidate`、私有接口配置和参考签名规则。
- Produces: `WechatPrivateApiClient.get_latest_articles()`, `extract_markdown()`, `WechatPrivateDailySource.discover_latest()`。

- [ ] **Step 1: 写签名、请求参数和响应适配失败测试**

```python
# tests/unit/test_wechat_private_client.py
import hashlib
import unittest
from unittest.mock import Mock

from services.wechat_private_client import WechatPrivateApiClient


class WechatPrivateApiClientTest(unittest.TestCase):
    def test_signing_matches_reference(self):
        client = WechatPrivateApiClient("key", "secret", clock=lambda: 1000)
        headers = client._get_headers("/api/latest_articles")
        expected = hashlib.md5(b"key/api/latest_articles1000secret").hexdigest()
        self.assertEqual(headers["x-signature"], expected)
        self.assertEqual(headers["x-timestamp"], "1000")

    def test_body_md5_part_matches_reference(self):
        body = b'{"names":["account"]}'
        client = WechatPrivateApiClient("key", "secret", clock=lambda: 1000)
        headers = client._get_headers("/api/example", body=body)
        body_md5 = hashlib.md5(body).hexdigest()
        expected = hashlib.md5(f"key/api/example1000{body_md5}secret".encode()).hexdigest()
        self.assertEqual(headers["x-signature"], expected)

    def test_latest_articles_uses_signed_get(self):
        session = Mock()
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"data": []}
        session.get.return_value = response
        client = WechatPrivateApiClient("key", "secret", session=session, clock=lambda: 1000)
        self.assertEqual(client.get_latest_articles("橘鸦Juya", count=5), {"data": []})
        session.get.assert_called_once_with(
            "https://wxcrawl.touchturing.com/api/latest_articles",
            headers=unittest.mock.ANY,
            params={"nickname": "橘鸦Juya", "count": 5, "offset": 0},
            timeout=(5, 20),
        )
```

```python
# tests/unit/test_wechat_daily_source.py
import unittest
from datetime import date
from unittest.mock import Mock

from services.ai_daily_source import DailySourceError
from services.wechat_daily_source import WechatPrivateDailySource


class WechatPrivateDailySourceTest(unittest.TestCase):
    def test_converts_latest_valid_article(self):
        client = Mock()
        client.get_latest_articles.return_value = {"data": [{
            "title": "今日标题【AI 早报 2026-07-10】",
            "link": "https://mp.weixin.qq.com/s/article-id",
            "create_time": 1783645200,
            "nickname": "橘鸦Juya",
        }]}
        result = WechatPrivateDailySource(client, "橘鸦Juya").discover_latest()
        self.assertEqual(result.issue_date, date(2026, 7, 10))
        self.assertEqual(result.article_url, "https://mp.weixin.qq.com/s/article-id")
        self.assertEqual(result.discovered_by, "wechat_private")

    def test_rejects_malformed_data_and_wrong_nickname(self):
        client = Mock()
        client.get_latest_articles.return_value = {"data": "bad"}
        with self.assertRaises(DailySourceError):
            WechatPrivateDailySource(client, "橘鸦Juya").discover_latest()
        client.get_latest_articles.return_value = {"data": [{
            "title": "标题【AI 早报 2026-07-10】",
            "link": "https://mp.weixin.qq.com/s/x", "create_time": 1783645200,
            "nickname": "其他账号",
        }]}
        with self.assertRaises(DailySourceError):
            WechatPrivateDailySource(client, "橘鸦Juya").discover_latest()
```

- [ ] **Step 2: 运行测试并验证模块不存在**

Run: `python -m unittest tests.unit.test_wechat_private_client tests.unit.test_wechat_daily_source -v`

Expected: FAIL with `ModuleNotFoundError`。

- [ ] **Step 3: 实现签名 HTTP 客户端**

```python
# services/wechat_private_client.py
import hashlib
import time

import requests


class WechatPrivateApiError(RuntimeError):
    pass


class WechatPrivateApiClient:
    def __init__(self, api_key, api_secret, base_url="https://wxcrawl.touchturing.com",
                 session=None, clock=time.time, timeout=(5, 20)):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.clock = clock
        self.timeout = timeout

    def _get_headers(self, endpoint, body=None):
        timestamp = str(int(self.clock()))
        body_md5 = hashlib.md5(body).hexdigest() if body else ""
        message = f"{self.api_key}{endpoint}{timestamp}{body_md5}{self.api_secret}"
        return {
            "x-api-key": self.api_key,
            "x-timestamp": timestamp,
            "x-signature": hashlib.md5(message.encode()).hexdigest(),
        }

    def get_latest_articles(self, nickname, count=5, offset=0):
        return self._get_json(
            "/api/latest_articles", {"nickname": nickname, "count": count, "offset": offset},
        )

    def extract_markdown(self, article_url):
        endpoint = "/api/extract"
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}", headers=self._get_headers(endpoint),
                params={"url": article_url}, timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise WechatPrivateApiError(f"微信私有接口请求失败: {type(exc).__name__}") from exc
        if response.text.startswith('"'):
            try:
                return response.json()
            except ValueError as exc:
                raise WechatPrivateApiError("微信私有接口 Markdown 响应无效") from exc
        return response.text

    def _get_json(self, endpoint, params):
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}", headers=self._get_headers(endpoint),
                params=params, timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise WechatPrivateApiError(f"微信私有接口请求失败: {type(exc).__name__}") from exc
        if not isinstance(payload, dict):
            raise WechatPrivateApiError("微信私有接口 JSON 响应不是对象")
        return payload
```

- [ ] **Step 4: 实现最新文章候选适配器**

```python
# services/wechat_daily_source.py
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from services.ai_daily_source import DailyIssueCandidate, DailySourceError
from services.wechat_private_client import WechatPrivateApiError

TITLE_DATE_RE = re.compile(r"【AI\s*早报\s*(\d{4}-\d{2}-\d{2})】")


class WechatPrivateDailySource:
    def __init__(self, client, nickname, count=5):
        self.client = client
        self.nickname = nickname
        self.count = count

    def discover_latest(self):
        try:
            payload = self.client.get_latest_articles(self.nickname, count=self.count)
        except WechatPrivateApiError as exc:
            raise DailySourceError(str(exc)) from exc
        items = payload.get("data")
        if not isinstance(items, list):
            raise DailySourceError("微信最新文章响应缺少 data 列表")
        candidates = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("nickname") and item.get("nickname") != self.nickname:
                continue
            title = item.get("title", "")
            match = TITLE_DATE_RE.search(title)
            article_url = item.get("link") or item.get("url") or ""
            if not match or not article_url.startswith("https://mp.weixin.qq.com/s/"):
                continue
            try:
                published_at = datetime.fromtimestamp(int(item.get("create_time")), ZoneInfo("Asia/Shanghai"))
            except (TypeError, ValueError, OSError):
                continue
            candidates.append(DailyIssueCandidate(
                title=title, article_url=article_url, published_at=published_at,
                issue_date=date.fromisoformat(match.group(1)), source_id=article_url,
                discovered_by="wechat_private",
            ))
        if not candidates:
            raise DailySourceError("微信私有接口未返回目标公众号的AI早报")
        return max(candidates, key=lambda item: item.published_at)
```

- [ ] **Step 5: 运行测试并提交**

Run: `python -m unittest tests.unit.test_wechat_private_client tests.unit.test_wechat_daily_source -v`

Expected: all PASS。

```powershell
git add -- services/wechat_private_client.py services/wechat_daily_source.py tests/unit/test_wechat_private_client.py tests/unit/test_wechat_daily_source.py
git commit -m "feat: add signed WeChat article discovery"
```

---

### Task 7: 启用双来源顺序和 Markdown 正文回退

**Files:**
- Modify: `services/ai_daily_factory.py`
- Modify: `services/wechat_article_service.py`
- Modify: `config.py`
- Modify: `tests/unit/test_ai_daily_factory.py`
- Modify: `tests/unit/test_wechat_article_service.py`

**Interfaces:**
- Consumes: Task 6 私有客户端/来源和 Task 2 HTML 正文服务。
- Produces: 最终 `wechat_private,bilibili` 顺序；只在传输或正文缺失时调用 Markdown extractor。

- [ ] **Step 1: 写私有来源优先和 Markdown 回退失败测试**

在 `test_ai_daily_factory.py` 添加：

```python
def test_private_source_precedes_bilibili_with_credentials(self):
    fake = SimpleNamespace(
        AI_DAILY_SOURCE_ORDER=["wechat_private", "bilibili"],
        BILIBILI_UPLOADER_MID=285286947,
        BILIBILI_UPLOADER_NAME="橘鸦Juya", BILIBILI_SEARCH_KEYWORD="橘鸦Juya",
        WECHAT_ACCOUNT_NICKNAME="橘鸦Juya", WECHAT_API_BASE_URL="https://private.example",
        WECHAT_API_KEY="fake-key", WECHAT_API_SECRET="fake-secret",
    )
    with patch("services.ai_daily_factory.config", fake):
        runtime = build_ai_daily_runtime()
    self.assertEqual([type(source).__name__ for source in runtime.discovery.sources], [
        "WechatPrivateDailySource", "BilibiliDailySource",
    ])
    self.assertIsNotNone(runtime.article_service.markdown_extractor)
```

在 `test_wechat_article_service.py` 添加 imports `requests` 和 `classify_rss_entry`，再添加：

```python
def test_transport_failure_uses_markdown_fallback(self):
    session = Mock()
    session.get.side_effect = requests.Timeout("timeout")
    markdown = """AI 早报 2026-07-10
=========
## 概览
### 要闻
标题 #1
## 标题 #1
正文
https://example.com/source
"""
    service = WechatArticleService(
        "橘鸦Juya", session=session, markdown_extractor=Mock(return_value=markdown),
    )
    result = classify_rss_entry(service.fetch(candidate()), keywords=[])
    self.assertEqual(result.all_items[0].category, "要闻")
    self.assertEqual(result.all_items[0].url, "https://example.com/source")

def test_account_mismatch_never_uses_markdown_fallback(self):
    extractor = Mock()
    service, _ = self.service(HTML.replace("橘鸦Juya", "其他账号"))
    service.markdown_extractor = extractor
    with self.assertRaises(WechatArticleError):
        service.fetch(candidate())
    extractor.assert_not_called()
```

- [ ] **Step 2: 运行测试并验证双来源和回退尚未接入**

Run: `python -m unittest tests.unit.test_ai_daily_factory tests.unit.test_wechat_article_service -v`

Expected: FAIL，来源顺序或 `markdown_extractor` 不符合断言。

- [ ] **Step 3: 将工厂升级为最终双来源配置**

`config.py` 默认顺序改为：

```python
AI_DAILY_SOURCE_ORDER = [
    item.strip()
    for item in os.getenv("AI_DAILY_SOURCE_ORDER", "wechat_private,bilibili").split(",")
    if item.strip()
]
```

`build_ai_daily_runtime()` 中，在 B 站实例之后组装：

```python
private_client = None
if config.WECHAT_API_KEY and config.WECHAT_API_SECRET:
    private_client = WechatPrivateApiClient(
        config.WECHAT_API_KEY, config.WECHAT_API_SECRET, config.WECHAT_API_BASE_URL,
    )
sources = []
for source_name in config.AI_DAILY_SOURCE_ORDER:
    if source_name == "wechat_private":
        if private_client:
            sources.append(WechatPrivateDailySource(private_client, config.WECHAT_ACCOUNT_NICKNAME))
    elif source_name == "bilibili":
        sources.append(bilibili)
    else:
        raise ValueError(f"未知AI早报来源: {source_name}")
if not sources:
    raise ValueError("AI早报没有可用来源；请启用 bilibili 或配置微信私有接口")
return AiDailyRuntime(
    discovery=DailyIssueDiscovery(sources, video_resolver=bilibili),
    article_service=WechatArticleService(
        config.WECHAT_ACCOUNT_NICKNAME,
        markdown_extractor=private_client.extract_markdown if private_client else None,
    ),
)
```

添加 `WechatPrivateApiClient`、`WechatPrivateDailySource` imports。

- [ ] **Step 4: 实现 Markdown 到现有分类器兼容 HTML 的转换**

给 `WechatArticleService.__init__` 增加并保存 `markdown_extractor=None`。`fetch()` 仅捕获 `WechatArticleTransportError`；有 extractor 时调用它并转到 `_from_markdown()`，公众号/日期不匹配的 `WechatArticleError` 不回退。

把 Task 2 中原 `fetch()` 的函数名改为 `_fetch_html()`，再新增公开 wrapper：

```python
def fetch(self, candidate):
    try:
        return self._fetch_html(candidate)
    except WechatArticleTransportError:
        if not self.markdown_extractor:
            raise
        markdown = self.markdown_extractor(candidate.article_url)
        return self._from_markdown(candidate, markdown)
```

```python
from html import escape


def markdown_to_content_html(markdown):
    lines = [line.strip() for line in markdown.splitlines()]
    output = []
    overview = False
    current_category = ""
    for line in lines:
        if not line or set(line) == {"="}:
            continue
        if line.startswith("## "):
            text = re.sub(r"[*_`]", "", line[3:]).strip()
            overview = text == "概览"
            current_category = ""
            output.append(f"<h2>{escape(text)}</h2>")
            continue
        if line.startswith("### "):
            current_category = re.sub(r"[*_`]", "", line[4:]).strip()
            output.append(f"<h3>{escape(current_category)}</h3>")
            continue
        if overview and current_category:
            numbers = re.findall(r"#(\d+)", line)
            if numbers:
                output.append("<ul>" + "".join(f"<li>#{n}</li>" for n in numbers) + "</ul>")
                continue
        if line.startswith("# "):
            output.append(f"<h1>{escape(re.sub(r'[*_`]', '', line[2:]).strip())}</h1>")
        else:
            output.append(f"<p>{escape(re.sub(r'[*_`]', '', line))}</p>")
    return "\n".join(output)
```

```python
def _from_markdown(self, candidate, markdown):
    match = DATE_RE.search(markdown)
    if not match or match.group(1) != candidate.issue_date.isoformat():
        raise WechatArticleError("私有接口 Markdown 日期不匹配")
    content_html = markdown_to_content_html(markdown)
    canonical = self._canonical_url(candidate.article_url)
    return RssEntry(
        title=candidate.issue_date.isoformat(), link=canonical,
        published=candidate.published_at.isoformat(), summary=candidate.title,
        content_html=content_html, content_text=html_to_text(content_html),
        entry_id=canonical, video_url=candidate.video_url,
        discovery_source=candidate.discovered_by,
    )
```

- [ ] **Step 5: 运行全部来源和正文测试并提交**

Run:

```powershell
python -m unittest tests.unit.test_ai_daily_factory tests.unit.test_wechat_article_service tests.unit.test_wechat_private_client tests.unit.test_wechat_daily_source tests.unit.test_bilibili_daily_source -v
```

Expected: all PASS。

```powershell
git add -- config.py services/ai_daily_factory.py services/wechat_article_service.py tests/unit/test_ai_daily_factory.py tests/unit/test_wechat_article_service.py
git commit -m "feat: enable WeChat discovery with bilibili fallback"
```

---

### Task 8: 部署文档、无 QQ 实时冒烟和完成审计

**Files:**
- Modify: `config.py:12-14`
- Create: `.env.example`
- Create: `scripts/smoke_test_ai_daily.py`
- Create: `docs/AI_Daily_Wechat_Push_20260710.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: 最终 `build_ai_daily_runtime()` 和分类器。
- Produces: 可重复运行且不会发送 QQ 的实时检查和完整配置说明。

- [ ] **Step 1: 移除已有硬编码 OpenAI Key 并添加无秘密配置样例**

`config.py` 改为：

```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.lkeap.cloud.tencent.com/v1")
```

创建：

```dotenv
# .env.example
NAPCAT_BASE_URL=http://127.0.0.1:23334
NAPCAT_WS_URL=ws://127.0.0.1:23334
NAPCAT_ACCESS_TOKEN=
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.lkeap.cloud.tencent.com/v1
AI_DAILY_SOURCE_ORDER=wechat_private,bilibili
BILIBILI_UPLOADER_MID=285286947
BILIBILI_UPLOADER_NAME=橘鸦Juya
BILIBILI_SEARCH_KEYWORD=橘鸦Juya
WECHAT_ACCOUNT_NICKNAME=橘鸦Juya
WECHAT_API_BASE_URL=https://wxcrawl.touchturing.com
WECHAT_API_KEY=
WECHAT_API_SECRET=
RSS_POLL_INTERVAL_SECONDS=300
RSS_FORWARD_USER_ID=1919447403
```

- [ ] **Step 2: 创建不会发送 QQ 的实时冒烟脚本**

```python
# scripts/smoke_test_ai_daily.py
import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.ai_daily_factory import build_ai_daily_runtime
from services.ai_daily_source import DailyIssueCandidate
from services.rss_filter_service import classify_rss_entry


def parse_args():
    parser = argparse.ArgumentParser(description="AI早报发现与微信正文冒烟测试（不会发送QQ）")
    parser.add_argument("--article-url")
    parser.add_argument("--video-url", default="")
    parser.add_argument("--date")
    return parser.parse_args()


def main():
    args = parse_args()
    runtime = build_ai_daily_runtime()
    if args.article_url:
        if not args.date:
            raise SystemExit("--article-url 必须同时提供 --date")
        issue_date = date.fromisoformat(args.date)
        candidate = DailyIssueCandidate(
            title=f"AI 早报 {args.date}", article_url=args.article_url,
            published_at=datetime.combine(issue_date, datetime.min.time(), ZoneInfo("Asia/Shanghai")),
            issue_date=issue_date, source_id=args.article_url,
            video_url=args.video_url, discovered_by="manual_smoke",
        )
    else:
        candidate = runtime.discovery.discover_latest()
    entry = runtime.article_service.fetch(candidate)
    result = classify_rss_entry(entry, keywords=[])
    if not result.all_items:
        raise SystemExit("正文未解析出新闻")
    categories = sorted({item.category for item in result.all_items})
    print(f"date={entry.title}")
    print(f"article={entry.link}")
    print(f"video={entry.video_url}")
    print(f"items={len(result.all_items)}")
    print("categories=" + ",".join(categories))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 写部署文档并在 README 增加入口**

`docs/AI_Daily_Wechat_Push_20260710.md` 写入以下完整章节内容，再补充 `.env.example` 每个变量的说明：

```markdown
# AI 早报微信/B站双来源推送

## 数据流
微信私有最新文章 → 失败时 B站投稿 → 微信正文 → 分类 → QQ 普通消息与合并转发。

## 最小配置
复制 `.env.example` 为 `.env`。只使用 B站时保持微信密钥为空；启用微信优先时填写服务分配的密钥，不要使用或提交 `client.py` 中的示例值。

## 运行与验证
- 启动：`python app.py`
- 单元测试：`python -m unittest discover -s tests/unit -p "test_*.py" -v`
- 最新一期实时检查：`python scripts/smoke_test_ai_daily.py`

## 回退行为
私有接口失败时继续 B站；B站 412 刷新匿名会话一次；微信正文校验失败或零新闻时不推送、不写状态；单群失败只重试该群。

## 状态迁移
旧 `data/rss_state.json` 在条目相同时迁移并保留去重；该文件已被 `.gitignore` 排除。
```

在 `README.md` 添加指向该文档的相对链接，不改写无关章节。

- [ ] **Step 4: 运行 2026-07-10 固定样本实时冒烟**

Run:

```powershell
python scripts/smoke_test_ai_daily.py --date 2026-07-10 --article-url "https://mp.weixin.qq.com/s/jeND4iYI0VXi7T-TF1CrWg" --video-url "https://www.bilibili.com/video/BV1YiNj6nE7n/"
```

Expected:

```text
date=2026-07-10
article=https://mp.weixin.qq.com/s/jeND4iYI0VXi7T-TF1CrWg
video=https://www.bilibili.com/video/BV1YiNj6nE7n/
items=27
categories=产品应用,开发生态,技术与洞察,模型发布,行业动态,要闻
```

- [ ] **Step 5: 运行最新一期发现并验证外部私有接口失败后的 B 站回退**

Run: `python scripts/smoke_test_ai_daily.py`

Expected: 输出一个 `mp.weixin.qq.com/s/...` 文章、同日 B 站视频和非零新闻数。若私有接口返回会话无效，日志先记录该来源失败，随后仍输出 B 站结果。

- [ ] **Step 6: 运行全套测试、编译、安全扫描和差异检查**

Run:

```powershell
python -m unittest discover -s tests/unit -p "test_*.py" -v
python -m compileall -q app.py config.py handlers services scripts tests/unit utils
git grep -n -E "(WECHAT_API_KEY|WECHAT_API_SECRET|OPENAI_API_KEY)\s*=\s*['\"][^'\"]+['\"]" -- ':!docs/superpowers/**'
git diff --check
git status --short
```

Expected:

- 全部单元测试 PASS。
- `compileall` exit 0，无输出。
- 敏感值扫描无匹配（exit 1）。
- `git diff --check` exit 0。
- 状态只包含本计划文件和用户原有无关改动；`.env`、`data/rss_state.json`、Cookie 不出现。

- [ ] **Step 7: 对照设计完成标准逐项审计**

记录并检查：

```text
1. B站发现：test_bilibili_daily_source + 最新一期 smoke
2. client.py 路径：test_wechat_private_client + test_wechat_daily_source
3. 来源回退：coordinator 测试 + 最新一期 smoke
4. 27条/六栏目/视频：固定样本 smoke
5. 自动/手动同链路：test_rss_handler + test_rss_push_service
6. 去重/部分群：test_rss_push_service
7. 无秘密/可编译：git grep + compileall + git status
```

任何证据缺失或冲突时，返回对应任务补失败测试并修复，不得声明完成。

- [ ] **Step 8: 提交部署说明和验证工具**

```powershell
git add -- config.py .env.example scripts/smoke_test_ai_daily.py docs/AI_Daily_Wechat_Push_20260710.md README.md
git commit -m "docs: add AI daily deployment and smoke checks"
```

## Final Verification Commands

```powershell
python -m unittest discover -s tests/unit -p "test_*.py" -v
python -m compileall -q app.py config.py handlers services scripts tests/unit utils
python scripts/smoke_test_ai_daily.py --date 2026-07-10 --article-url "https://mp.weixin.qq.com/s/jeND4iYI0VXi7T-TF1CrWg" --video-url "https://www.bilibili.com/video/BV1YiNj6nE7n/"
python scripts/smoke_test_ai_daily.py
git diff --check
git status --short
```

自动化验证不得调用真实 QQ 群发送；只有用户明确要求生产发送时才能执行该外部写操作。
