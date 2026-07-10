from dataclasses import dataclass

import config
from services.ai_daily_source import DailyIssueDiscovery
from services.bilibili_daily_source import BilibiliDailySource
from services.wechat_article_service import WechatArticleService
from services.wechat_daily_source import WechatPrivateDailySource
from services.wechat_private_client import WechatPrivateApiClient


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
    private_client = None
    if config.WECHAT_API_KEY and config.WECHAT_API_SECRET:
        private_client = WechatPrivateApiClient(
            config.WECHAT_API_KEY,
            config.WECHAT_API_SECRET,
            config.WECHAT_API_BASE_URL,
        )

    sources = []
    for source_name in config.AI_DAILY_SOURCE_ORDER:
        if source_name == "bilibili":
            sources.append(bilibili)
        elif source_name == "wechat_private":
            if private_client:
                sources.append(
                    WechatPrivateDailySource(
                        private_client,
                        config.WECHAT_ACCOUNT_NICKNAME,
                    )
                )
        else:
            raise ValueError(f"未知AI早报来源: {source_name}")

    if not sources:
        raise ValueError("AI早报没有可用来源；请启用 bilibili 或配置微信私有接口")

    return AiDailyRuntime(
        discovery=DailyIssueDiscovery(sources, video_resolver=bilibili),
        article_service=WechatArticleService(
            config.WECHAT_ACCOUNT_NICKNAME,
            markdown_extractor=(private_client.extract_markdown if private_client else None),
        ),
    )
