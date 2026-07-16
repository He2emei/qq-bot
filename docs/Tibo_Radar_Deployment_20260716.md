# Tibo Radar 部署说明

Tibo Radar 是独立于 AI 早报的轻量监控任务。它支持 TwitterAPI.io 和 Apify 两种 provider，获取 `@thsottiaux` 新动态，排除原生转推、保留原创帖、引用帖和回复，并只发送到 QQ 群 `1105591264`。

`twitterapi` 模式使用 `tweet_filter` WebSocket 实时流，并用 `advanced_search` 补漏。`apify` 模式通过 Store Actor 定时读取最近数条时间线，属于免费额度内的低频抓取方案，不启动 TwitterAPI.io WebSocket。

## 配置

API key 只写入 tai261 的 `/root/tai/qq-bot/.env`：

```dotenv
TIBO_RADAR_PROVIDER=twitterapi
TIBO_RADAR_API_KEY=
TIBO_RADAR_API_BASE_URL=https://api.twitterapi.io
TIBO_RADAR_HANDLE=thsottiaux
TIBO_RADAR_GROUP_ID=1105591264
TIBO_RADAR_POLL_INTERVAL_SECONDS=900
TIBO_RADAR_STATE_PATH=data/tibo_radar_state.json
TIBO_RADAR_BOOTSTRAP_SEND=false
TIBO_RADAR_STREAM_ENABLED=true
TIBO_RADAR_WEBSOCKET_URL=wss://ws.twitterapi.io/twitter/tweet/websocket
TIBO_RADAR_RULE_TAG=qq-bot-tibo-radar
TIBO_RADAR_RULE_INTERVAL_SECONDS=5

# 切换 Apify 时改为 TIBO_RADAR_PROVIDER=apify，并配置：
TIBO_RADAR_APIFY_API_TOKEN=
TIBO_RADAR_APIFY_API_BASE_URL=https://api.apify.com
TIBO_RADAR_APIFY_ACTOR_ID=seemuapps~x-tweet-scraper
TIBO_RADAR_APIFY_MAX_ITEMS=25
TIBO_RADAR_APIFY_POLL_INTERVAL_SECONDS=28800
TIBO_RADAR_APIFY_RUN_TIMEOUT_SECONDS=180
```

所选 provider 没有对应凭据时调度器安全禁用，不进行网络请求或 QQ 发送。首次启用默认只建立水位，不补发旧帖；之后按 tweet ID 和群号去重。两个 provider 共享同一状态文件，因此切换不会重复推送已经完成的帖子。发送失败不丢失，下次轮询会先重试。

Apify Free 模式默认每 8 小时最多取 25 条，遵守该 Actor 对免费用户“每天 3 次、每次 25 条、间隔至少 30 分钟”的限制。按公开价 `$1/1000 tweets` 做保守估算，满额约 `$2.25/30天`；2026-07-16 从 tai261 实测一次返回 25 条，运行费用为 `$0.0002`。它由每月 `$5` 免费额度覆盖，但发现延迟约 8 小时，且单个 8 小时窗口超过 25 条时仍可能漏帖。

## 1 分钟尝试触发的 Apify 增量影子验证

`maximedupre~twitter-scraper` 支持 `sinceId`，空增量实测不产生结果费。仓库提供独立的只读影子任务：

- `scripts/tibo_radar_apify_shadow.py` 每次只运行一轮；
- `deploy/tibo-radar-apify-shadow.timer` 按墙钟每分钟尝试触发；oneshot service 仍在运行时 systemd 不会启动并发实例，因此实际间隔由 Actor 的 1～4 分钟耗时决定；
- `deploy/tibo-radar-apify-shadow-stop.timer` 在 48 小时后自动停用抓取 timer，脚本自身也有 48 小时硬截止；
- 状态写入 `data/tibo_radar_apify_shadow_state.json`；
- 对账日志写入 `data/tibo_radar_apify_shadow_observations.jsonl`；
- 日志保存帖子 ID、时间、原创/回复/引用分类、URL、Actor 运行耗时与可用的实际费用，不保存正文；纯转推按 Radar 产品规则在上游排除；
- Actor 错误也写入 JSONL，但不会推进增量水位；
- 不导入 QQ sender，不会向群发送消息。

密钥单独放在权限为 `0600` 的 `/root/tai/qq-bot/.env.tibo-shadow`：

```dotenv
TIBO_RADAR_APIFY_API_TOKEN=
TIBO_RADAR_HANDLE=thsottiaux
TIBO_RADAR_APIFY_API_BASE_URL=https://api.apify.com
TIBO_RADAR_APIFY_MAX_ITEMS=10
TIBO_RADAR_APIFY_RUN_TIMEOUT_SECONDS=300
```

启用前复制两组 service/timer 到 `/etc/systemd/system/`，执行 daemon-reload 后同时启动抓取 timer 和 stop timer。48 小时后任务自动停止，再根据 JSONL 与现有信源对账；切换正式 Radar 是另一个独立步骤。

## 验证

先运行不发送 QQ 的测试：

```bash
venv/bin/python -m unittest tests.unit.test_tibo_radar_service tests.unit.test_tibo_radar_factory tests.unit.test_tibo_radar_stream tests.unit.test_apify_tibo_source tests.unit.test_tibo_radar_scheduler -v
```

启用 key 并重启后检查：

```bash
grep -a 'Tibo Radar' /root/tai/qq-bot/run.log | tail -n 30
cat /root/tai/qq-bot/data/tibo_radar_state.json
```

日志出现“已建立初始水位”代表信源验证成功且没有补发旧帖。下一条新动态成功发送后，日志会记录 tweet ID，状态文件会记录群 `1105591264` 的投递时间。

## 日志轮转

仓库中的 `deploy/qq-bot.logrotate` 应安装到 `/etc/logrotate.d/qq-bot`。配置按天或达到 20 MiB 轮转，保留 14 份并压缩；使用 `copytruncate`，不要求为轮转重启机器人。
