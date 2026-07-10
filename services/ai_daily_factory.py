from dataclasses import dataclass

import config
from services.ai_daily_source import DailyIssueDiscovery
from services.bilibili_daily_source import BilibiliDailySource
from services.wechat_article_service import WechatArticleService


@dataclass(frozen=True)
class AiDailyRuntime:
    discovery: DailyIssueDiscovery
    article_service: WechatArticleService


def build_ai_daily_runtime() -> AiDailyRuntime:
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
                raise RuntimeError("wechat_private 来源将在私有微信适配器接入后启用")
        else:
            raise ValueError(f"未知AI早报来源: {source_name}")

    if not sources:
        raise ValueError("AI早报没有可用来源；请启用 bilibili")

    return AiDailyRuntime(
        discovery=DailyIssueDiscovery(sources, video_resolver=bilibili),
        article_service=WechatArticleService(config.WECHAT_ACCOUNT_NICKNAME),
    )
