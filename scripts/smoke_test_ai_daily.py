"""Read-only smoke test for the AI Daily discovery and article parser."""
import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ai_daily_factory import build_ai_daily_runtime
from services.ai_daily_source import DailyIssueCandidate
from services.rss_filter_service import classify_rss_entry


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="验证 AI 早报发现和解析，不发送 QQ 消息")
    parser.add_argument("--date", help="指定日期，格式 YYYY-MM-DD；需同时提供 --article-url")
    parser.add_argument("--article-url", help="指定微信文章链接，跳过发现流程")
    parser.add_argument("--video-url", default="", help="与指定文章关联的 B 站视频链接")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if bool(args.date) != bool(args.article_url):
        raise SystemExit("--date 和 --article-url 必须同时提供")

    runtime = build_ai_daily_runtime()
    candidate = _explicit_candidate(args) if args.article_url else runtime.discovery.discover_latest()
    entry = runtime.article_service.fetch(candidate)
    result = classify_rss_entry(entry, keywords=[])

    categories = sorted({item.category or "未分类" for item in result.all_items})
    print(f"早报日期: {entry.title}")
    print(f"发现来源: {entry.discovery_source or candidate.discovered_by}")
    print(f"文章链接: {entry.link}")
    print(f"视频链接: {entry.video_url or '无'}")
    print(f"新闻条数: {len(result.all_items)}")
    print(f"分类: {', '.join(categories) if categories else '无'}")
    return 0


def _explicit_candidate(args) -> DailyIssueCandidate:
    issue_date = date.fromisoformat(args.date)
    return DailyIssueCandidate(
        title=f"AI 早报 {issue_date.isoformat()}",
        article_url=args.article_url,
        published_at=datetime(
            issue_date.year,
            issue_date.month,
            issue_date.day,
            9,
            0,
            tzinfo=ZoneInfo("Asia/Shanghai"),
        ),
        issue_date=issue_date,
        source_id=args.article_url,
        video_url=args.video_url,
        discovered_by="smoke_test",
    )


if __name__ == "__main__":
    raise SystemExit(main())
