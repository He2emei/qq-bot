# Tibo Radar 部署说明

Tibo Radar 是独立于 AI 早报的轻量轮询任务。它通过 TwitterAPI.io 的 `advanced_search` 获取 `@thsottiaux` 新动态，排除原生转推、保留原创帖、引用帖和回复，并只发送到 QQ 群 `1105591264`。

当前实现是第一阶段轮询 MVP：每 5 分钟搜索并带 5 分钟重叠窗口补漏。完整目标仍是 `tweet_filter` 实时推送作为主发现、`advanced_search` 每 15–30 分钟补漏；在实时规则和 API key 完成端到端验证前，不应把轮询 MVP 标记为最终方案。

## 配置

API key 只写入 tai261 的 `/root/tai/qq-bot/.env`：

```dotenv
TIBO_RADAR_API_KEY=
TIBO_RADAR_API_BASE_URL=https://api.twitterapi.io
TIBO_RADAR_HANDLE=thsottiaux
TIBO_RADAR_GROUP_ID=1105591264
TIBO_RADAR_POLL_INTERVAL_SECONDS=300
TIBO_RADAR_STATE_PATH=data/tibo_radar_state.json
TIBO_RADAR_BOOTSTRAP_SEND=false
```

没有 `TIBO_RADAR_API_KEY` 时调度器安全禁用，不进行网络请求或 QQ 发送。首次启用默认只建立水位，不补发最近 24 小时的旧帖；之后按 tweet ID 和群号去重。发送失败不会记为完成，下次轮询继续重试。

## 验证

先运行不发送 QQ 的测试：

```bash
venv/bin/python -m unittest tests.unit.test_tibo_radar_service tests.unit.test_tibo_radar_factory -v
```

启用 key 并重启后检查：

```bash
grep -a 'Tibo Radar' /root/tai/qq-bot/run.log | tail -n 30
cat /root/tai/qq-bot/data/tibo_radar_state.json
```

日志出现“已建立初始水位”代表信源验证成功且没有补发旧帖。下一条新动态成功发送后，日志会记录 tweet ID，状态文件会记录群 `1105591264` 的投递时间。

## 日志轮转

仓库中的 `deploy/qq-bot.logrotate` 应安装到 `/etc/logrotate.d/qq-bot`。配置按天或达到 20 MiB 轮转，保留 14 份并压缩；使用 `copytruncate`，不要求为轮转重启机器人。
