# RSS 重点信息筛选说明 202606030007

## 更新概述

本次新增 RSS 信息筛选节点，用于将完整早报中的新闻拆分为：

- 重点信息
- 非重点信息

展示方式暂不处理，当前只输出结构化分类结果。

## 重点判断规则

一条新闻会被归为重点，只要满足以下任一条件：

1. 信息源在概览中已标注为 `要闻`
2. 新闻标题或正文命中 RSS 重点关键词

默认关键词：

```text
Claude
DeepSeek
Codex
Gemini
Antigravity
```

## 新增配置

新增数据文件：

```text
data/rss_keywords.json
```

结构：

```json
{
  "keywords": [
    "Claude",
    "DeepSeek",
    "Codex",
    "Gemini",
    "Antigravity"
  ]
}
```

`config.py` 的 `DATA_PATHS` 中新增：

```python
'rss_keywords': 'data/rss_keywords.json'
```

## 新增服务

新增：

```text
services/rss_filter_service.py
```

主要对象：

- `RssNewsItem`
  - 单条新闻结构
  - 包含编号、标题、链接、分类、正文、是否重点、命中关键词等字段

- `RssFilterResult`
  - 分类结果
  - 包含 `important_items` 和 `other_items`

- `RssKeywordStore`
  - 负责关键词增删改查

主要函数：

- `classify_rss_entry(entry, keywords=None)`
  - 对一个 RSS 条目进行重点/非重点分类

- `extract_news_items(entry, keywords)`
  - 从完整 HTML 正文中提取新闻条目

## 新增 QBot 指令

新增 handler：

```text
handlers/rss_handler.py
```

新增命令：

```text
#rsskw list
#rsskw add <关键词1> [关键词2] ...
#rsskw del <关键词1> [关键词2] ...
#rsskw edit <旧关键词> <新关键词>
#rsskw set <关键词1> [关键词2] ...
#rsskw clear
#rsskw help
```

命令用途：

- `list`：查看当前关键词
- `add`：追加关键词，自动跳过重复项
- `del`：删除关键词，大小写不敏感
- `edit`：修改单个关键词
- `set`：覆盖设置关键词
- `clear`：清空关键词

## 验证结果

使用以下 RSS 源验证：

```text
https://imjuya.github.io/juya-ai-daily/rss.xml
```

在默认关键词下，最新一期 `2026-06-02`：

- 重点：7 条
- 非重点：27 条

其中：

- `#1`、`#2`、`#3` 来自信息源 `要闻`
- 其他重点来自关键词命中，例如 `Codex`、`Claude`

## 测试

新增：

```text
tests/unit/test_rss_filter_service.py
```

覆盖：

- 信息源 `要闻` 自动归为重点
- 关键词命中自动归为重点
- 未命中项归为非重点
- 关键词存储的添加、删除、修改、覆盖和清空

已执行：

```powershell
python -m unittest tests.unit.test_rss_service tests.unit.test_rss_filter_service
python -m compileall -q app.py handlers\rss_handler.py services\rss_filter_service.py services\rss_service.py tests\unit\test_rss_filter_service.py
```

结果均通过。
