# RSS Feedparser 获取节点说明 202606022024

## 更新概述

本次更新为后续“从 RSS 信息源获取信息并发送到 QQ 群”的流程打通第一步：RSS 信源拉取和条目解析。

当前只实现获取节点，不包含：

- QQ 群发送
- 定时轮询
- 已发送条目去重
- 消息格式模板

## 新增依赖

在 `requirements.txt` 中新增：

```text
feedparser==6.0.12
```

## 新增模块

新增 `services/rss_service.py`，提供：

- `RssEntry`
  - 统一 RSS 条目结构
  - 字段包括 `title`、`link`、`published`、`summary`、`entry_id`

- `RssFetchError`
  - RSS 获取或解析失败时抛出的异常

- `fetch_rss_entries(feed_url, limit=None, timeout=15)`
  - 使用 `requests` 拉取 RSS 内容
  - 使用 `feedparser` 解析 RSS/Atom
  - 返回标准化后的 `RssEntry` 列表

## 当前验证源

本次使用以下 RSS 源进行真实拉取验证：

```text
https://imjuya.github.io/juya-ai-daily/rss.xml
```

验证结果：

- 可成功获取 RSS XML
- 可成功解析最新条目
- 最新条目标题示例：`2026-06-02`
- 最新条目链接示例：`https://imjuya.github.io/juya-ai-daily/issue-109/`

## 测试

新增 `tests/unit/test_rss_service.py`，覆盖：

- RSS 条目字段标准化
- `limit` 参数截断
- 网络请求失败时抛出 `RssFetchError`

已执行：

```powershell
python -m unittest tests.unit.test_rss_service
python -m compileall -q services\rss_service.py tests\unit\test_rss_service.py
```

结果均通过。

## 后续计划

下一步建议实现已发送条目去重，例如：

- 新增 `data/rss_seen.json`
- 以 `entry_id` 或 `link` 作为唯一键
- 只发送未见过的新条目

之后再接入 QQ 群发送和定时轮询。
