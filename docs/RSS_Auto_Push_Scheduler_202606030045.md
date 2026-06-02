# RSS 自动推送调度说明 202606030045

## 更新概述

本次新增 RSS 自动轮询推送能力。

RSS 源本身是拉取式信息源。当前流程不会被 RSS 源主动通知，而是在 QQ Bot 启动后由本地调度器定时检查最新条目。

默认行为：

- 每 60 秒检查一次 RSS 最新条目
- 如果最新条目没有推送过，则推送到指定群聊
- 推送成功后记录最新条目 ID，避免重复发送

## 新增配置

`config.py` 新增：

```python
RSS_PUSH_GROUP_IDS = [GROUP_IDS['default']]
RSS_POLL_INTERVAL_SECONDS = 60
RSS_FORWARD_USER_ID = int(os.getenv("RSS_FORWARD_USER_ID", "1919447403"))
```

说明：

- `RSS_PUSH_GROUP_IDS`
  - RSS 自动推送群列表
  - 当前默认使用 `GROUP_IDS['default']`

- `RSS_POLL_INTERVAL_SECONDS`
  - RSS 检查间隔
  - 当前为 60 秒

- `RSS_FORWARD_USER_ID`
  - 合并转发自定义节点使用的用户 ID
  - 可通过环境变量覆盖

## 新增状态文件

新增运行时状态文件：

```text
data/rss_state.json
```

该文件记录：

- `last_entry_id`
- `last_title`
- `last_link`
- `updated_at`

用于避免每次轮询重复推送同一期内容。

该文件已加入 `.gitignore`，不会提交到仓库。

## 新增服务

新增：

```text
services/rss_push_service.py
```

主要函数：

- `check_and_push_latest_rss(force=False)`
  - 获取最新 RSS 条目
  - 检查是否已经推送
  - 未推送时发送普通重点消息和合并转发消息
  - 写入状态文件

- `push_rss_entry(entry, group_ids)`
  - 推送指定 RSS 条目到指定群聊

新增：

```text
services/rss_scheduler.py
```

主要函数：

- `start_rss_scheduler()`
  - 启动 RSS 后台调度器

- `check_rss_update_job()`
  - 每分钟执行一次 RSS 更新检查

## App 启动集成

`app.py` 启动时会尝试启动 RSS 调度器：

```python
from services.rss_scheduler import start_rss_scheduler
start_rss_scheduler()
```

如果调度器启动失败，会打印错误，但不会阻止 Flask 服务启动。

## 手动触发复用

`#rssdaily` 现在复用 `push_rss_entry()`，因此手动触发和自动推送使用同一套展示逻辑。

## 测试

新增：

```text
tests/unit/test_rss_push_service.py
```

覆盖：

- 状态文件记录最新条目 ID
- 同一条目不会重复推送
- `force=True` 可以强制推送

已执行：

```powershell
python -m unittest tests.unit.test_rss_service tests.unit.test_rss_filter_service tests.unit.test_rss_display_service tests.unit.test_rss_push_service
python -m compileall -q app.py handlers\rss_handler.py services\rss_push_service.py services\rss_scheduler.py services\rss_display_service.py utils\api_utils.py tests\unit\test_rss_push_service.py
```

结果均通过。

## 验证情况

使用 mock 方式验证推送流程：

- 普通重点消息调用 1 次
- 合并转发消息调用 1 次
- 合并转发节点数为 8
- 默认推送群为 `638227713`

未实际连接 NapCat 发送 QQ 消息。
