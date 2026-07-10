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


def video(
    title="今日标题【AI 早报 2026-07-10】",
    description="相关链接：https://mp.weixin.qq.com/s/article-id",
):
    return {
        "mid": 285286947,
        "author": "橘鸦Juya",
        "title": title,
        "description": description,
        "bvid": "BV1YiNj6nE7n",
        "pubdate": 1783649249,
    }


class BilibiliDailySourceTest(unittest.TestCase):
    def test_encodes_non_ascii_keyword_in_referer_header(self):
        session = Mock()
        session.headers = {}

        BilibiliDailySource(285286947, "橘鸦Juya", "橘鸦Juya", session=session)

        self.assertEqual(
            session.headers["Referer"],
            "https://search.bilibili.com/all?keyword=%E6%A9%98%E9%B8%A6Juya",
        )

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
        self.assertEqual(result.discovered_by, "bilibili")
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
        source, session = self.make_source(
            [
                FakeResponse(),
                FakeResponse(status_code=412),
                FakeResponse(),
                FakeResponse(payload=payload),
            ]
        )

        result = source.discover_latest()

        self.assertEqual(result.source_id, "BV1YiNj6nE7n")
        self.assertEqual(session.get.call_count, 4)

    def test_coordinator_falls_back_and_enriches_video(self):
        first = Mock()
        first.discover_latest.side_effect = DailySourceError("private unavailable")
        candidate = DailyIssueCandidate(
            title="t",
            article_url="https://mp.weixin.qq.com/s/x",
            published_at=datetime.fromisoformat("2026-07-10T09:00:00+08:00"),
            issue_date=date(2026, 7, 10),
            source_id="x",
            discovered_by="fallback",
        )
        second = Mock()
        second.discover_latest.return_value = candidate
        resolver = Mock()
        resolver.find_by_date.return_value = "https://www.bilibili.com/video/BV123/"

        result = DailyIssueDiscovery([first, second], resolver).discover_latest()

        self.assertEqual(result.video_url, "https://www.bilibili.com/video/BV123/")


if __name__ == "__main__":
    unittest.main()
