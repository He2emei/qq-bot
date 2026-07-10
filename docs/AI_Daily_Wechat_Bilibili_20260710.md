# AI 早报双来源恢复说明

## 工作方式

机器人不再依赖已经失效的 RSS 地址，而是按 `AI_DAILY_SOURCE_ORDER` 发现最新一期早报：

1. `wechat_private`：可选的已签名微信私有接口，按公众号昵称取得文章列表；
2. `bilibili`：搜索橘鸦 Juya 的公开视频，读取当天标题与简介中的微信公众号文章链接。

默认顺序是 `wechat_private,bilibili`。未配置 `WECHAT_API_KEY` 和 `WECHAT_API_SECRET` 时，第一项会被自动跳过，B 站仍可独立工作。

发现文章后，机器人首先直接读取微信公众号页面，校验公众号昵称与标题日期；只有网络失败或页面结构异常时，才会通过私有接口请求 Markdown 正文。账号或日期校验不通过不会启用 Markdown 回退。

## 配置

复制 `.env.example` 为 `.env`，至少保留下列公开默认值：

```dotenv
AI_DAILY_SOURCE_ORDER=wechat_private,bilibili
BILIBILI_UPLOADER_MID=285286947
BILIBILI_UPLOADER_NAME=橘鸦Juya
BILIBILI_SEARCH_KEYWORD=橘鸦Juya
WECHAT_ACCOUNT_NICKNAME=橘鸦Juya
```

如需启用私有微信路径，再在本机 `.env` 中填写：

```dotenv
WECHAT_API_BASE_URL=https://wxcrawl.touchturing.com
WECHAT_API_KEY=
WECHAT_API_SECRET=
```

密钥只保存在 `.env` 或部署环境变量中，不应写入代码、日志或提交记录。若私有接口暂时不可用，可将来源顺序改为 `bilibili`，持续使用公开 B 站发现路径。

OpenAI 调用也从本机环境读取 `OPENAI_API_KEY`；如使用非默认兼容服务，可通过 `OPENAI_BASE_URL` 覆盖服务地址。

## 只读烟测

以下命令仅发现、获取和解析文章，绝不会向 QQ 群发送消息：

```powershell
python scripts/smoke_test_ai_daily.py
```

针对已知文章进行固定验证时：

```powershell
python scripts/smoke_test_ai_daily.py `
  --date 2026-07-10 `
  --article-url https://mp.weixin.qq.com/s/jeND4iYI0VXi7T-TF1CrWg `
  --video-url https://www.bilibili.com/video/BV1YiNj6nE7n/
```

成功时会输出发现来源、文章与视频链接、解析出的新闻条数和分类。自动推送依旧使用现有调度器、目标群配置和 `data/rss_state.json` 去重状态；状态记录已细化到“每一期 × 每个群”，发生部分群失败时下次会只重试失败群。
