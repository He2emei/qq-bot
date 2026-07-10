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
    """Raised when a daily-news source cannot provide a valid candidate."""


class DailySource(Protocol):
    def discover_latest(self) -> DailyIssueCandidate: ...


class VideoResolver(Protocol):
    def find_by_date(self, issue_date: date) -> str: ...


class DailyIssueDiscovery:
    """Try configured sources in order and attach a same-day video when available."""

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
