#!/usr/bin/env python3
# scripts/export_rss_markdown.py
import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.rss_service import fetch_rss_entries


DEFAULT_FEED_URL = "https://imjuya.github.io/juya-ai-daily/rss.xml"
DEFAULT_OUTPUT_DIR = Path("temp") / "rss_exports"


def _safe_filename(value: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*\s]+', "_", value.strip())
    filename = filename.strip("._")
    return filename or "rss_entry"


def export_latest_rss_markdown(feed_url: str, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    entries = fetch_rss_entries(feed_url, limit=1)
    if not entries:
        raise RuntimeError(f"RSS源没有条目: {feed_url}")

    entry = entries[0]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{_safe_filename(entry.title)}.md"

    markdown = (
        f"# {entry.title}\n\n"
        f"- RSS源: {feed_url}\n"
        f"- 原文链接: {entry.link}\n"
        f"- 发布时间: {entry.published}\n"
        f"- 条目ID: {entry.entry_id}\n\n"
        "---\n\n"
        f"{entry.content_text}\n"
    )

    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="导出最新 RSS 条目的完整正文为 Markdown。")
    parser.add_argument("--feed-url", default=DEFAULT_FEED_URL, help="RSS源URL")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Markdown输出目录",
    )
    args = parser.parse_args()

    output_path = export_latest_rss_markdown(args.feed_url, Path(args.output_dir))
    print(output_path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
