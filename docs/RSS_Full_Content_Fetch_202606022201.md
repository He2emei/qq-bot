# RSS 全文获取节点说明 202606022201

## 更新概述

本次更新将 RSS 获取节点从“只读取摘要”扩展为“读取完整早报正文”。

此前 `RssEntry.summary` 只对应 RSS 的 `description/summary` 字段。以橘鸦 AI 早报为例，该字段只有约 359 字，并且会在概览处截断。

本次改为额外读取 `entry.content[0].value`，该字段包含完整 HTML 正文。

## 代码变更

`services/rss_service.py` 中的 `RssEntry` 新增字段：

- `content_html`
  - RSS 条目的完整 HTML 正文

- `content_text`
  - 由 `content_html` 转换得到的纯文本
  - 保留图片 URL
  - 保留链接 URL
  - 将列表项、引用块和分隔线转换成适合 QQ 消息的文本格式

新增辅助函数：

- `html_to_text(html)`
  - 将 RSS HTML 正文转换成纯文本

## 验证结果

使用以下 RSS 源验证：

```text
https://imjuya.github.io/juya-ai-daily/rss.xml
```

最新条目验证结果：

- 标题：`2026-06-02`
- `summary` 长度：约 359 字符
- `content_html` 长度：约 50034 字符
- `content_text` 长度：约 30559 字符
- 纯文本末尾包含第 34 条和最终提示，确认已获取完整正文

## 测试

已更新 `tests/unit/test_rss_service.py`，覆盖：

- `content:encoded` 全文读取
- HTML 正文转换为纯文本
- 图片 URL 保留
- 链接 URL 保留

已执行：

```powershell
python -m unittest tests.unit.test_rss_service
python -m compileall -q services\rss_service.py tests\unit\test_rss_service.py
```

结果均通过。

## 后续计划

下一步可以进入发送前处理：

- QQ 单条消息长度控制
- 全文分段发送
- 去重状态记录
- 定时轮询
