# Tibo Radar 低延迟替代方案调研

> 日期：2026-07-16（Asia/Shanghai）  
> 目标：在 tai261 不直连 X、不维护 X 登录态的前提下，把发现延迟从 Apify Free 当前约 8 小时降到 30 分钟以内；优先免费，其次极低成本。

## 结论

8 小时不是 Apify Free 平台本身的限制，而是当前选中的 `seemuapps/x-tweet-scraper` Actor 对 Free 用户设置了“每天最多 3 次”的产品限制。更合适的选择有三档：

1. **最稳妥：恢复 TwitterAPI.io WebSocket 为实时主源，把补漏从 15 分钟降频到 6–24 小时。** WebSocket 只按命中的帖子收费，预计秒级到分钟级；6 小时一次空查询的最低月费约 `$0.018`，加上 Tibo 实际帖子仍只是几分钱量级。代价是最低一次充值 `$10`，但不是月费，余额不过期。
2. **现有 Apify Free 下可行：改用 `maximedupre/twitter-scraper` 的 `sinceId` 增量查询。** 2026-07-16 实测成功返回 Tibo 最新 4 条，实际扣费 `$0.0004`；随后以最新 ID 查询，31 秒返回 0 条、实际扣费 `$0`。因此可以按 5–15 分钟轮询，费用近似只随新帖数增长，而不是随轮询次数增长。它仍是社区 Actor，先灰度对账 48 小时再替换生产源。
3. **最正规：X 官方按量 API，经 Cloudflare Worker 或 GitHub Actions 做境外出口。** 官方读取 Post 为 `$0.005/条`，同一资源 24 小时内重复读取只计一次；如果使用 `since_id` 只取增量，月成本主要取决于 Tibo 实际发帖量，例如 10 条/天约 `$1.50/月`。数据最权威，但仍需 X Developer App 和预付 credits，不是免费。

如果目标是“稳定、低延迟、少维护”，第 1 条明显优于继续搜刮免费镜像。若坚持只用现有 Apify Free 额度，先让已通过单次实测的 `maximedupre` 连续 48 小时与现有源对账；合格后即可把轮询设为 5 分钟。

## 候选方案对比

| 方案 | 典型延迟 | 估算月成本 | X 登录 | 主要风险 | 建议 |
|---|---:|---:|---|---|---|
| TwitterAPI.io WebSocket + 6h 补漏 | 秒级～分钟 | 约 `$0.02` 起 | 不需要 | 非官方供应商；需一次充值 | **生产首选** |
| Apify `maximedupre` + `sinceId` | 5～15min | `$0.0001/新帖`；空查 `$0` | 不需要 | 社区 Actor，长期可靠性未知 | **48h 灰度首选** |
| Apify `jacquemus` | 不可用 | 本次失败扣 `$0.00004` | 不需要 | GraphQL query id 已失效 | 排除 |
| Apify `fastcrawler`，4 条/15min | ≤15min | `$2.07` 理论值 | 不需要 | 商店评分 1.9/5 | 不优先 |
| Apify `scrape.badger`，5 条/30min | ≤30min | 结果费约 `$1.08` + compute | 不需要 | 另收 `$0.20/CU`，需先测单次 CU | 可 PoC |
| X 官方 API + Worker 桥 | 1～15min | 10 条/天约 `$1.50` | Developer App，不是用户登录 | 要购买 X credits；桥需保密 | 正规备选 |
| SocialData Search 增量 | ≤30min | `$0.0002/新帖` | 不需要 | Search 当前 Limited Access | 获准后很强 |
| TwitterAPIs / GetXAPI | ≤30min | 约 `$1.15` / `$1.44` | 不需要 | 小供应商、需预付或试用 | 第二梯队 PoC |
| Cloudflare Worker + 公共 Nitter RSS | 1～15min | `$0` | 我方不需要 | 公共实例依赖其账号池、随时限流/下线 | 只作辅助源 |
| GitHub Actions + 公共 Nitter RSS | 5～30min | 公共仓库 `$0` | 我方不需要 | cron 可能延迟/丢弃；共享 IP；状态和密钥治理 | 临时 PoC |
| 自建 Nitter/RSSHub | 5～30min | 主机成本低 | **需要真实 X 会话** | token 失效、封号、代理维护 | 不符合边界 |
| snscrape / 匿名 guest API | 不可用 | `$0` | 无 | 上游公开时间线已不可访问 | 排除 |
| LinkedIn / OpenAI 官方更新 | 不确定 | `$0` | 通常需登录或只可人工看 | 不是 Tibo X 的等价镜像 | 只作重大公告旁路 |

## 1. 现有 TwitterAPI.io：真正的低成本实时方案

当前实现的 Custom Filter Rule + WebSocket 与按账号 `$29/月` Stream 套餐不是同一个产品。官方 WebSocket 文档说明规则命中的 tweet 按 REST 相同方式计费；公开价格为每返回 tweet 15 credits，即 `$0.15/1000`，普通 REST 调用最低 15 credits。[TwitterAPI.io WebSocket 说明](https://twitterapi.io/blog/using-websocket-for-real-time-twitter-data)、[价格](https://twitterapi.io/pricing)

现在 `$0.432/月` 的主要来源，是每 15 分钟做一次即使无结果也收最低费用的补漏，而不是 WebSocket 常驻连接。把补漏改为：

- 启动时一次；
- WebSocket 断线重连后一次；
- 正常情况下每 6 小时一次；

则空查询最低费用为 `4 次/天 × 30 天 × $0.00015 = $0.018/月`。即使 Tibo 每天 20 条，实时命中费用也只有约 `$0.09/月`。这条路线同时满足低延迟、无需 X 登录、tai261 性能占用极低。

缺点不是月费，而是充值门槛：公开 Payment 页面最低单次 top-up 为 `$10`；充值 credits 不过期。以 `$0.10/月` 粗算可用多年，但仍需接受供应商风险。[充值页](https://twitterapi.io/payment)、[订阅与 credits](https://twitterapi.io/subscribe)

## 2. Apify Free：换 Actor，而不是接受 8 小时

Apify Free 每月提供 `$5` 平台额度且超额硬阻断；不同 Store Actor 可以另外规定 Free 用户次数。Apify 官方说明，Pay-per-event Actor 通常已把平台计算成本包含在事件单价中，但必须以每个 Actor 的 Pricing 区域为准，并可为每次运行设置最大扣费上限。[Apify Store Actor 计费模型](https://docs.apify.com/actors/running/actors-in-store)、[Apify 价格](https://apify.com/pricing)

### 2.1 `jacquemus/x-tweet-scraper`

商店页声称无需 X API key、无需登录，支持按 username 获取帖子，标价从 `$0.10/1000 results`；同步 API 也已公开。[Actor API 页](https://apify.com/jacquemus/x-tweet-scraper/api)

成本上界按“每轮都返回并重复计费 4 条”计算：

- 30 分钟：`4 × 48 × 30 × $0.0001 = $0.576/月`
- 15 分钟：`4 × 96 × 30 × $0.0001 = $1.152/月`
- 5 分钟：`4 × 288 × 30 × $0.0001 = $3.456/月`

因此它在纸面上甚至能用 Apify Free 做 5 分钟轮询。但 2026-07-16 实测失败，日志明确显示 X GraphQL 返回 404，Actor 使用的 query id / feature flags 已失效；本次失败费用 `$0.00004`。在作者更新前排除，不再进入灰度。

### 2.2 `maximedupre/twitter-scraper`

商店页明确支持 profile URL/search URL，按每个返回 post、profile 或 trend `$0.0001` 收费；初始化或首屏失败时以 0 行结束，不收 dataset item 事件费用，并支持设置全局最大条数。[Actor 商店页](https://apify.com/maximedupre/twitter-scraper)

实测输入 `fromUsers=["thsottiaux"]`、包含原创/引用/回复、排除纯转推，最大 4 条：运行约 88 秒，准确返回 Tibo 最新 4 条，账单事件为 4 个 dataset item，共 `$0.0004`。随后把最新 `postId` 作为 `sinceId` 再运行，约 31 秒返回 0 条，账单 `$0`。输出含 `postId`、`postUrl`、`postText`、`postDateTime`、`replyToPostId`、引用关系和媒体字段，足够接入现有 Radar。

这意味着正式实现可把 `sinceId` 持久化到现有状态文件，5 分钟轮询每月约 8,640 次，但空轮询不消耗美元额度；若 Tibo 每月产生 1,000 条原创/回复，结果费也只有 `$0.10`。限制从“每天 3 次”变成了 Actor 的长期稳定性，因此仍需保留深回填或第二信源，并先做 48 小时只读对账。

### 2.3 其他 Actor

- `fastcrawler/tweet-x-twitter-scraper-0-2-1k-pay-per-result-v2` 标价约 `$0.18/1000`；4 条/15 分钟约 `$2.0736/月`，价格仍在 Free 额度内，但商店评分约 1.9/5，因此不应先选。[Actor API 页](https://apify.com/fastcrawler/tweet-x-twitter-scraper-0-2-1k-pay-per-result-v2/api/cli)
- `scrape.badger/twitter-tweets-scraper` 对 Free 层公开标价 `$0.15/1000 results`，支持 Advanced Search 和 `max_results`，没有公开的每日运行次数限制；5 条/30 分钟的结果费约 `1440 × 5 × $0.00015 = $1.08/月`。但该 Actor 还收 `$0.20/CU` 平台计算费用，是否能压在剩余 `$3.92` 内取决于单次实际 CU，必须先跑一次再外推。[Actor pricing](https://apify.com/scrape.badger/twitter-tweets-scraper/pricing)
- `xquik/x-tweet-scraper` 对 Free 层为 `$0.015/tweet`，即使每 30 分钟只返回 1 条也约 `$21.60/月`；它的高折扣只给付费层，不合适。[xquik pricing](https://apify.com/xquik/x-tweet-scraper/pricing)
- `altimis/scweet` Free 最多 10 runs/day 且每次最少 100 条，`apidojo/twitter-profile-scraper` Free demo 每月最多 5 次，都无法承担 30 分钟轮询。[Scweet](https://apify.com/altimis/scweet)、[Apidojo profile scraper](https://apify.com/apidojo/twitter-profile-scraper)
- 原先 `dami_studio/tweet-scraper` 的理论成本也能压在 `$5` 内，但 tai261 已实测被 X 返回 `BLOCKED`，纸面价格没有意义。
- 现用 `seemuapps/x-tweet-scraper` 单次很便宜，但 Free 用户每天最多 3 次，所以无法通过调低 `maxItems` 换取更高频率；8 小时是该 Actor 的产品上限，不是我们的调度问题。[Actor 页](https://apify.com/seemuapps/x-tweet-scraper)

### 2.4 PoC 验收方式

对两个新 Actor 各运行 48 小时，先用 30 分钟频率，单次 `maxItems=4`，每次设置 `maxTotalChargeUsd`：

1. 与现有 TwitterAPI.io 或人工时间线逐条按 tweet ID 对账；
2. 单独统计原创、回复、引用、转推是否齐全；
3. 记录实际 `usageTotalUsd`、运行时长、空结果/错误 envelope；
4. 连续 12 次成功后再升到 15 分钟；
5. 任一 Actor 连续两次漏掉相同帖子、字段漂移或出现 BLOCKED，就不升为主源。

## 3. 境外计算出口：能解决网络，不能创造数据

### Cloudflare Workers

Workers Cron Trigger 支持 `* * * * *` 每分钟运行，也给出了 `*/30` 示例；Free 计划每天 100,000 次请求、最多 5 个 Cron Trigger、单次 10 ms CPU、128 MB 内存。网络等待不等于 CPU 计算，但复杂浏览器抓取显然不适合 10 ms 限额。[Cron Trigger](https://developers.cloudflare.com/workers/configuration/cron-triggers/)、[Workers 限额](https://developers.cloudflare.com/workers/platform/limits/)

一个轻量 Worker 可以：

- 通过 `fetch()` 调 X 官方 API、第三方 API 或某个 Nitter RSS；
- 用 Cron 每 5–15 分钟拉取；
- 把最新 tweet ID 和规范化 JSON 写入 KV/D1，tai261 只读这个桥。

KV Free 每天允许 1,000 次写、100,000 次读，5 分钟一次仅 288 次写/天，足够；D1 Free 的读写额度也远高于此场景。[Workers KV 价格](https://developers.cloudflare.com/kv/platform/pricing/)、[D1 价格](https://developers.cloudflare.com/d1/platform/pricing/)

但 Worker 的出口 IP/数据中心由 Cloudflare 调度，不是专属稳定住宅 IP；它不能保证 X 或公共 Nitter 不封锁。若上游仍是社区镜像，Worker 只是把“tai261 访问不了”改成“Cloudflare 暂时访问得了”。

### GitHub Actions

GitHub scheduled workflow 最短间隔 5 分钟，但官方明确说高负载时会延迟，严重时队列中的任务可能被丢弃；公共仓库的标准 hosted runner 免费且不限分钟，私有仓库 GitHub Free 每月仅 2,000 分钟，而每个 job 的不足一分钟也向上取整。[schedule 限制](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)、[runner 免费条件](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)、[分钟取整](https://docs.github.com/en/actions/how-tos/monitor-workflows/view-job-execution-time)

按每 5 分钟一个 job 算，私有仓库最多约 `8,640` 个计费分钟/月，远超 2,000 分钟；公共仓库虽免费，但 workflow 和脚本会公开，所有 tai261 webhook secret 必须放 GitHub Secrets，状态不能提交成频繁变动的公开 commit。GitHub runner 还是 Azure 共享动态 IP，官方提醒共享基础设施可能影响第三方 IP reputation。[runner IP](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-githubs-ip-addresses)

所以 GitHub Actions 适合做 48 小时验证：每 10–15 分钟拉 Nitter 或 Actor API，再推向 tai261；不适合当需要严格 SLA 的长期实时调度器。Cloudflare Worker 更轻、更连续。

## 4. 匿名 X 抓取、Nitter 与 RSSHub 的现实边界

`snscrape` 维护者已明确说明：公开 Twitter 时间线已无法抓取，匿名 guest token 不能再生成；未来最多可能支持单条帖子和个人页的热门帖子，而不是完整时间线。[snscrape 项目维护者说明](https://github.com/JustAnotherArchivist/snscrape/issues/1037)

Nitter README 也明确写明，Twitter 移除旧方法后，运行 Nitter 实例需要真实账号和 session token；它还需要 Redis/Valkey。Nitter 能提供 RSS，但账号池由实例运营者承担，公共实例不是无上游成本的正式 API。[Nitter README](https://github.com/zedeus/nitter)

RSSHub 的 X 用户路由同样依赖 `TWITTER_AUTH_TOKEN`/cookie 或可用的 X GraphQL 代理。项目 issue 记录过 token 有效但几天后时间线变空、GraphQL query ID 变化等故障；2026 年虽修过动态 query ID，仍没有消除会话和反爬依赖。[RSSHub X route issue 与修复](https://github.com/DIYgod/RSSHub/issues/18894)、[token 故障样本](https://github.com/DIYgod/RSSHub/issues/19210)

因此可以让 Cloudflare/GitHub 去读公共 Nitter RSS，获得 5–15 分钟的零成本辅助信号，但不能把它描述为可靠主源。自建 Nitter/RSSHub 会重新引入用户明确不想维护的 X 登录态。

## 5. X 官方 API + 境外桥

X 现在对自助 API 使用按量 credits：Post read 为 `$0.005/资源`，没有月费或最低月消费；同一资源在 24 小时内重复读取只计一次。官方用户时间线端点 `GET /2/users/:id/tweets` 支持较高请求频率，所有 API v2 端点都需要 Developer App 鉴权。[X API 价格](https://docs.x.com/x-api/getting-started/pricing)、[Developer Console 与 24 小时去重](https://docs.x.com/fundamentals/developer-portal)、[rate limits](https://docs.x.com/x-api/fundamentals/rate-limits)

最直接的实现不是反复读取整页时间线，而是 Recent Search 查询 `from:thsottiaux`，持久化响应的 `meta.newest_id`，随后每 5–30 分钟把它作为 `since_id`。X 官方分页指南就是这样增量轮询；空轮询返回 0 个 Post，按“返回资源”计费，因此轮询频率本身不产生 Post read 费用。不要加 `-is:reply`，这样 Tibo 的回复也会被 `from:` 匹配。[官方增量分页模式](https://docs.x.com/x-api/posts/search/integrate/paginate)、[Recent Search endpoint](https://docs.x.com/x-api/posts/search-recent-posts)、[查询 operators](https://docs.x.com/x-api/posts/search/integrate/operators)

Bearer Token 放在 Cloudflare secret，Worker 只允许固定查询 `@thsottiaux`，tai261 不能传任意 query。费用近似等于新帖子数：

- 5 条/天：`5 × 30 × $0.005 = $0.75/月`
- 10 条/天：`$1.50/月`
- 30 条/天：`$4.50/月`

换言之，`$5` 可购买约 1,000 个新 Post read，约等于 33 条/天；这不是 X 提供的免费额度，只是和 Apify Free 的 `$5` 预算作横向比较。

这比 TwitterAPI.io 贵，但比社区 Actor 更权威，而且轮询频率本身不直接放大已去重资源的费用。是否存在单次最低购入金额需以 Developer Console 实际页面为准；公开文档只说明预付 credits、无月度最低消费。[X Usage and Billing](https://docs.x.com/x-api/fundamentals/post-cap)

## 6. Tibo 的其他公开渠道

目前没有找到由 Thibault Sottiaux 本人确认、与 `@thsottiaux` 自动同步的 Bluesky、Mastodon、个人 RSS 或博客。可确认的另一个职业渠道是 LinkedIn 个人页，但 LinkedIn 活动并不是 X 的完整转发，而且页面常要求登录；不能用它替代 Tibo X 时间线。[Thibault Sottiaux 的 LinkedIn](https://www.linkedin.com/in/thibault-sottiaux-27195366)

OpenAI 官方 Codex changelog、OpenAI News、Forum/活动页可覆盖重大产品公告，但不包含 Tibo 的大量回复和即时观点。它们应作为“官方 Codex 更新”旁路，消息必须明确标注来源，不能伪装成 Tibo 发帖：

- [Codex changelog](https://developers.openai.com/codex/changelog)
- [OpenAI News](https://openai.com/news/)
- [OpenAI Forum](https://forum.openai.com/)

## 7. 其他按量 API

下面几家都能把 30 分钟轮询的月成本压到几美元以内，但规模、准入和长期稳定性弱于 X 官方或已实测的 TwitterAPI.io，只适合并行 PoC。

### SocialData

使用 Search `from:thsottiaux since_id:<last_id>`，而不是每次拉完整时间线。官方计费是 `$0.0002/返回 tweet`；无数据请求每分钟前三次免费，30 分钟轮询远低于此限制，所以成本近似等于新帖数量，`$5` 可覆盖 25,000 条新帖。问题是 Search 和 user-tweets 文档目前标记 **Limited Access**，注册后未必立即可调用。[Search](https://docs.socialdata.tools/reference/get-search-results/)、[pricing](https://docs.socialdata.tools/getting-started/pricing/)、[rate limits](https://docs.socialdata.tools/getting-started/rate-limits/)

### TwitterAPIs

其 Advanced Search 支持 `from:thsottiaux` 与增量游标，官方定价信息为约 `$0.0008/call`、新账号 `$0.50` credits；30 分钟轮询 `1440` 次/月约 `$1.152/月`，赠额理论上约维持 13 天。它是小型第三方服务，必须先确认回复覆盖、空结果收费和 tai261 可达性。[官方文档](https://docs.twitterapis.com/docs)、[Search reference](https://docs.twitterapis.com/docs/reference/search)

### GetXAPI

其 `user/tweets_and_replies` 是目标最匹配的接口，公开价格 `$0.001/call`、每次约 20 条；30 分钟轮询约 `$1.44/月`。新账号赠 `$0.10`，最低购买 `$10`，credits 不过期。成本可以接受，但最低购买与现有 TwitterAPI.io 相同，且供应商验证样本更少，因此没有理由在未做对账前直接替换现有源。[GetXAPI pay-per-use pricing](https://www.getxapi.com/pay-per-use-pricing)

### ApiTwitter

其 server-side cookie/proxy pool 的 user tweets 接口公开标价约 `$0.14/1000 read calls`，最低请求费 `$0.00005`；按 1440 次/月，纸面成本约 `$0.07–0.20/月`，但最低 top-up 为 `$10`，而 user-tweets 文档没有明确承诺包含回复。应先验证 reply coverage 才能列为备源。[Introduction](https://docs.apitwitter.com/introduction)、[user tweets pool](https://docs.apitwitter.com/api-reference/endpoint/tweets/get-user-tweets-pool)、[billing](https://docs.apitwitter.com/billing)

## 推荐的下一步

1. 保持当前生产源不变，对 `maximedupre` 做 48 小时、先 15 分钟后 5 分钟频率的只读灰度对账；每次传上次最大 `postId` 作为 `sinceId`，并设置单次最大扣费。
2. 灰度达标后，把它切为 5 分钟主轮询，保留 `seemuapps` 每天 1 次、25 条深回填；后者每天一次低于其 Free 的 3 次上限。
3. 若 `maximedupre` 出现连续漏帖、字段漂移或 X 协议失效，不再继续轮换社区抓取器：恢复 TwitterAPI.io WebSocket，并把补漏降到 6 小时。这是当前综合成本最低、延迟最好的付费兜底。
4. 如果未来要求供应商和数据许可更正规，申请 X Developer App，用 Cloudflare Worker 做固定目标的境外桥；不要在 tai261 自建浏览器、Nitter 或 X 会话池。
