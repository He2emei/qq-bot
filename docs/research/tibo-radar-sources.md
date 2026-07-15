# Tibo Radar 信源调研

> 调研日期：2026-07-16（Asia/Shanghai）
> 目标：在 `tai261.xjtumc.com` 上可靠发现并转发 Tibo 的最新公开 X 帖子，尽量不让服务器直连 X，也不在服务器维护 X 登录态。

## 已确认的产品边界

- Tibo Radar 作为独立功能实现，不与 AI 早报的来源、状态文件、展示逻辑或目标群配置耦合。
- 第一阶段只向 QQ 群 `1105591264`（AI-xjtu）推送；不向 AI 早报当前配置的其他群发送。
- 可以复用项目的 APScheduler、NapCat 消息发送工具，以及“按事件 × 按群记录投递完成状态”的通用做法，但使用独立的配置项和状态存储。

## 与现有远程部署的衔接约束

2026-07-11 的 AI 早报版本是通过受控文件清单同步到 tai261，而不是通过 Git 更新。部署时保留了远程 `.env`、`data/`、定制 `app.py`、私聊发送能力和状态查询能力，并对 `utils/api_utils.py` 做了人工三方合并。服务器已实际运行新版早报链路，但 Git 仍停留在 `53fed17`，工作树包含大量修改和未跟踪文件。

所以 Tibo Radar 不应直接建立在“远程 Git 比本地落后，可以覆盖更新”的假设上。实施前必须先审计并收编远程专属改动，建立可追溯部署基线；之后才同步独立的 Tibo 模块。部署过程中仍需保留 `.env`、`data/` 和现有状态文件，并在切换前运行完整单测、只读信源烟测以及单实例检查。

## 结论

首选 **TwitterAPI.io 的 `tweet_filter` 推送规则**，规则使用 `from:thsottiaux`，并以 `advanced_search` 做低频补漏。它不要求 X 登录，只需供应商 API key；`api.twitterapi.io` 已从 tai261 实测可达。对于只监控一个低频账号，推送比反复请求最近 20 条的 `last_tweets` 更省钱，也更接近实时。

建议的降级链是：

1. TwitterAPI.io `tweet_filter`（主发现源，Webhook 或 WebSocket）；
2. TwitterAPI.io `advanced_search`（定时补漏、冷启动回填）；
3. SocialData Search 或 user tweets（第二供应商故障切换；需先确认时间线端点的准入）；
4. Sorsa `/user-tweets`（可用但最低套餐对单账号偏贵）；
5. OpenAI Codex changelog / OpenAI 官方页面（只报告产品动态，不冒充 Tibo 本人发帖）。

不建议把 RSSHub 公共实例、公共 Nitter、X syndication、oEmbed 或搜索引擎作为生产主源。它们分别存在服务器不可达、需要上游 X 账号、接口未获支持、无法发现新帖、结果不完整/许可受限等问题。

## 身份核验

- 人物是 **Thibault “Tibo” Sottiaux**。OpenAI Forum 的官方活动页称其为 OpenAI MTS，并明确说他领导 Codex；OpenAI Build Week 页面列出 Thibault Sottiaux 为 Head of Product & Platform。[OpenAI Forum](https://forum.openai.com/public/events/codex-is-for-everyone-why-codex-matters-beyond-code-fa40puy7wi)、[OpenAI Build Week](https://openai.com/build-week/)
- X handle 是 **`@thsottiaux`**。X 自身索引页显示该账号名为 Tibo，简介为“Codex & ChatGPT @OpenAI”。[X profile](https://x.com/thsottiaux)
- 因此规范化目标应保存为 `handle=thsottiaux`，帖子唯一键使用 X tweet/post ID，而不是正文哈希。

## tai261 与当前网络实测

测试时间为 2026-07-16。HTTP 测试均使用普通桌面 User-Agent、20–25 秒超时；未携带任何 X cookie 或供应商 key。无 key 时返回 401/403，反而证明 DNS、TLS 和应用层链路可达。

| 候选 | 当前工作机 | tai261 | 含义 |
|---|---:|---:|---|
| `x.com` | 未作为候选直连依赖 | 超时/失败 | 服务器不能直接依赖 X |
| `syndication.twitter.com/.../thsottiaux` | 200，返回约 349 KB HTML | 25 s 超时 | 不能部署为源 |
| `publish.twitter.com/oembed` | 200，重定向到 `publish.x.com` | TLS 失败 | 即使可达也只能按已知 URL 查单帖 |
| `rsshub.app/twitter/user/thsottiaux/...` | 404 | 25 s 超时 | 公共实例没有可用的该路由，服务器也不可达 |
| `nitter.net/thsottiaux/rss` | 200，20 项；最新项为 2026-07-15 05:59:46 UTC | 25 s 超时 | 数据新鲜但 tai261 不可达 |
| `nitter.poast.org` | 未复测 | 超时/失败 | 换公共实例未解决网络问题 |
| `xcancel.com/thsottiaux/rss` | 200 后转到 `rss.xcancel.com`，内容要求 RSS reader 白名单 | 连接失败 | 不能匿名直接使用 |
| Google Search | 200 后落到 `google.com.hk` | 25 s 超时 | 服务器不可用 |
| Bing Search | 本机未作为主源验证 | 200，约 0.41 s | 可达，但结果质量和使用许可不合格 |
| `api.twitterapi.io` | 未带 key | 403 API key required，约 0.75 s | **可达，适合 PoC** |
| `api.socialdata.tools` | 未带 key | 401，约 0.75 s | 可达，适合备用 PoC |
| `api.sorsa.io` | 未带 key | 403 missing key，约 0.77 s | 可达，适合备用 PoC |
| `api.apify.com` | 未带 key | 401，约 0.91 s | 平台可达；具体 Actor 仍需另行选型 |

补充：tai261 约有 3.6 GiB 内存、测试时 available 约 1.4 GiB、无 swap。轻量轮询/接收 Webhook 没问题，但没有必要为了一个账号运行浏览器或维护 Nitter + Redis + X 会话池。

部分失败域名的 DNS 结果也可疑：测试时 `syndication.twitter.com` 解析到 `31.13.92.37`（Meta 网段），`rsshub.app` 解析到 `128.121.243.76`。这提示问题不只是目标站封禁，也可能包含 DNS 污染/境外路由异常；仅轮换 Nitter 域名不能从根本上改善可靠性。

## 候选信源评估

### 1. TwitterAPI.io：推荐主源

官方文档提供三种有用能力：

- `GET /twitter/user/last_tweets`：按用户名取最近帖子，每页最多 20 条，按创建时间排序；用 `X-API-Key` 认证。文档明确提醒：如果单账号需要非常频繁地取最新帖，不要使用这个端点，应改用实时监控方案。[Get User Last Tweets](https://docs.twitterapi.io/api-reference/endpoint/get_user_last_tweets)
- `GET /twitter/tweet/advanced_search`：可以用 `from:thsottiaux` 和 `since_time` / `until_time` 做增量回填；供应商官方示例就是每 5 分钟监控指定账号。[官方监控示例](https://twitterapi.io/blog/how-to-monitor-twitter-accounts-for-new-tweets-in-real-time)
- `POST /oapi/tweet_filter/add_rule` 与 Webhook/WebSocket：规则可设为 `from:thsottiaux -filter:retweets`（是否排除回复需按产品需求决定），以数秒级间隔推送匹配项；WebSocket 使用 `x-api-key`，同一 key 只允许一条活动连接。[监控指南](https://twitterapi.io/blog/monitoring-twitter-via-api-guide)、[WebSocket 指南](https://twitterapi.io/blog/using-websocket-for-real-time-twitter-data)

当前公开价格是帖子 **$0.15 / 1,000 条**，1 美元等于 100,000 credits；每个返回帖 15 credits，普通调用最低 15 credits（$0.00015）。[TwitterAPI.io pricing](https://twitterapi.io/pricing)

运维判断：

- 对一个账号优先使用 `tweet_filter`，接收后立刻按 tweet ID 幂等入库并回 2xx；QQ 转发放到异步任务中。
- 每 15–30 分钟用 `advanced_search` 对“上次成功水位前移 5 分钟”做重叠补漏，避免 Webhook 短暂失败造成永久丢帖。
- 不要每 5 分钟调用 `last_tweets`：若每次都返回 20 条，按现价约为 `$0.003/次`，30 天约 8,640 次，即约 **$25.92/月**；`advanced_search` 的窄时间窗或推送更符合该场景。
- 供应商关于延迟和可靠性的描述是自述，PoC 必须实测 7–14 天，记录 Tibo 发帖时间、首次收到时间、漏帖数和重复数。

风险：这是非 X 官方的数据供应商；数据抓取方式、字段和价格都可能变化。不得把 API key 写入仓库或日志，需设置月度预算/用量告警，并保留第二供应商切换点。

### 2. SocialData：推荐第二供应商

SocialData 的用户帖子端点为 `GET /twitter/user/{user_id}/tweets`，使用 `Authorization: Bearer ...`，公开账号通常每页约 20 条；但该页面当前标记 **Limited Access**，并建议需要灵活过滤时使用 Search 的 `from:USERNAME` 查询。[User tweets](https://docs.socialdata.tools/reference/get-user-tweets-replies/)

其公开计费是大多数资源 `$0.0002/返回项`，账户需保持正余额；失败请求不扣余额。无数据请求每分钟前三次不收费，超过后可能按固定请求价计费。[SocialData pricing](https://docs.socialdata.tools/getting-started/pricing/)

优点是 tai261 可达、按量付费且接口简单。缺点是时间线端点准入受限。因此 PoC 应先用 Search 验证 `from:thsottiaux` 的覆盖和排序，再决定是否申请 user tweets 权限。它适合在 TwitterAPI.io 连续失败后切换，而不是同时双份高频抓取。

### 3. Sorsa：可用但单账号不经济

Sorsa 用 `ApiKey` header；`POST https://api.sorsa.io/v3/user-tweets` 接收用户链接或 ID，按最新到最旧分页，官方建议用它轮询单账号。[API reference](https://docs.sorsa.io/api-reference-guide)、[Real-time monitoring](https://docs.sorsa.io/real-time-monitoring)

公开最低 Starter 套餐为 `$49/月`、10,000 requests、20 req/s；`/user-tweets` 约返回 20 条。[Sorsa pricing](https://docs.sorsa.io/pricing)

它从 tai261 可达，接口也满足需求，但固定月费对单个低频账号明显高于按量供应商。除非未来扩展到大量账号或主/备供应商 SLA 有更高要求，否则只保留适配器位置，不先购买。

### 4. RSSHub：可作为转换层，但解决不了上游访问

RSSHub 的目标路由确实是 `/twitter/user/:id/:routeParams?`，并支持排除回复/转推。[RSSHub route docs](https://rsshub-doc.pages.dev/en/social-media)

但当前源代码表明该路由要求配置 `TWITTER_AUTH_TOKEN` 或 X consumer key/secret；也可配置 `TWITTER_THIRD_PARTY_API`。其所谓 third-party API 是一个兼容 X Web GraphQL 路径的代理基址，并非 TwitterAPI.io/SocialData 这类结构化数据 API。代码随后仍调用 UserByScreenName、UserTweets 等 GraphQL 操作。[user route source](https://github.com/DIYgod/RSSHub/blob/master/lib/routes/twitter/user.ts)、[API selection source](https://github.com/DIYgod/RSSHub/blob/master/lib/routes/twitter/api/index.ts)、[web API source](https://github.com/DIYgod/RSSHub/blob/master/lib/routes/twitter/api/web-api/api.ts)

所以在 tai261 自建 RSSHub 仍需要 X cookie/官方 key/一个可用的 X GraphQL 反代；公共实例又已实测 404/超时。项目已有 RSS 消费能力不代表必须把新信源先转 RSS：直接增加一个小型 provider adapter 更轻，也能保留供应商原始 tweet ID 和媒体字段。

### 5. Nitter / XCancel：仅作人工诊断

Nitter 支持 RSS、页面轻量，但项目 README 已明确：Twitter 移除旧方法后，**运行实例需要真实账号和 session tokens**；它使用非官方 API，还需要 Redis/Valkey。[Nitter source/README](https://github.com/zedeus/nitter)

本机 `nitter.net` 能拿到 Tibo 的新鲜 RSS，说明它可作为人工交叉核验；tai261 对多个实例超时，不能做自动源。自建则重新引入了用户最想避免的 X 登录态、代理和 token 维护，而且 Nitter 是 AGPL-3.0，若修改并对网络用户提供服务需评估相应源码提供义务。

XCancel 的 RSS 当前要求邮件申请 reader 白名单，tai261 又连接失败，因此也不适合无人值守部署。

### 6. X syndication / oEmbed：不能负责“发现”

X 官方支持的 oEmbed 接口把一个**已知帖子 URL**转换成嵌入 HTML，例如 `https://publish.x.com/oembed?url=...`。[X oEmbed docs](https://docs.x.com/x-for-websites/embedded-posts/overview)

它不能列出用户最新帖子，所以最多在上游已经给出 tweet ID 后用于补全/合规展示。`syndication.twitter.com/srv/timeline-profile/...` 当前会返回完整 HTML，但没有公开、稳定的 timeline 数据 API 合同；而且 tai261 实测不可达。不应解析其中的内部 JSON 作为生产依赖。

### 7. 搜索引擎索引：不适合作为 Radar

Bing 从 tai261 可达，但 `format=rss&q=site:x.com/thsottiaux/status` 实测返回 Yahoo Mail 等无关结果，没有 Tibo 帖子。该 RSS 响应自身的版权声明还限定为个人、非商业 RSS 聚合展示，其他使用需微软许可。Google 从服务器超时。搜索索引还天然有分钟到数天的不确定延迟、删除残留和排序漂移，因此不能作为完整性或实时性来源。

## 官方 OpenAI 替代信号

这些源无法复刻 Tibo 的个人观点，但适合作为“主源故障期间仍不漏重大 Codex 公告”的旁路：

- [Codex changelog](https://developers.openai.com/codex/changelog)
- [OpenAI news](https://openai.com/news/)
- [OpenAI Build Week](https://openai.com/build-week/)
- [OpenAI Forum 的 Codex 活动](https://forum.openai.com/public/events/codex-is-for-everyone-why-codex-matters-beyond-code-fa40puy7wi)

消息中必须标注来源类型，例如“OpenAI 官方更新”，不能伪装成“来自 Tibo 的 X 动态”。

## 推荐实现边界与降级策略

建议把信源与 QQ 发送解耦为统一事件：

```text
provider -> normalize(tweet_id, author, text, created_at, url, media, source)
         -> idempotency store (tweet_id)
         -> optional translation/summary
         -> QQ delivery + delivery status
```

运行策略：

1. 主 provider 接受 TwitterAPI.io 推送；持久化原始 payload 的必要字段和 `received_at`。
2. 补漏 job 用上次成功的 `created_at` 减去 5 分钟查询，按 tweet ID 去重；游标只在整批处理成功后推进。
3. 主 provider 连续 3 次失败或 30 分钟无成功心跳时，启用 SocialData；恢复后先 backfill 再切回。
4. 两个 X provider 都故障时，仅发送官方 Codex 更新，并发出内部健康告警；不要用 Bing 的猜测结果自动转发。
5. 媒体下载失败不应阻塞文字转发；原始 X URL 可保留，但国内用户可能打不开，消息应至少含完整文本。

如果将来这些托管 API 也从 tai261 不可达，下一选择不是在 tai261 跑浏览器，而是在境外无服务器函数/轻量主机放一个采集桥：只负责调用供应商或读取 Nitter/syndication，向 tai261 暴露带签名的极小 JSON/RSS。这个桥不需要浏览器，性能开销很小；代价是多一个需监控的部署点和对桥接数据访问控制的责任。

## 法律、合规与安全注意事项

- 第三方 API 能技术访问，不等于自动获得无限转载许可。上线前应审阅供应商服务条款、X 的 [Developer Agreement and Policy](https://developer.x.com/en/developer-terms/agreement-and-policy) 以及目标 QQ 群的使用性质；本报告不是法律意见。
- 仅转发公开账号的公开帖；不尝试绕过 protected account、删除状态或访问控制。
- 尽量保存 tweet ID、必要正文、时间和来源，不长期镜像不必要的画像/互动数据；删除或纠正机制应能按 tweet ID 操作。
- API key 只放服务器 secret/environment，日志对 header 和响应中的敏感字段做脱敏；分别设置超时、重试上限、熔断和月度预算。
- 对非官方供应商必须保留 provenance（如 `source=twitterapi.io`）和原始 X URL，避免把供应商数据误称为 X 官方 API 结果。

## PoC 验收标准

先用 TwitterAPI.io 的试用额度跑 7–14 天，不立即实现多供应商全套：

- tai261 连续运行，无浏览器、无 X cookie；
- 新原创帖/回复/转推的纳入规则有明确测试；
- 95% 帖子在目标延迟内到达（建议先定 2 分钟），零永久漏帖，重复转发为零；
- 重启、Webhook 500、网络断开后能靠 backfill 恢复；
- 记录每次调用、返回帖子数和 credits，给出真实月成本外推；
- 与人工查看 `@thsottiaux` 或可用 Nitter RSS 每日对账一次。

若 PoC 达标，再实现 SocialData provider；若不达标，先比较缺失是供应商覆盖、过滤规则还是本地幂等/投递问题，而不是直接在 tai261 上部署浏览器或 Nitter。
