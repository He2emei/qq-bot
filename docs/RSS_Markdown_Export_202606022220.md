# RSS Markdown 导出说明 202606022220

## 更新概述

本次新增 RSS 最新条目 Markdown 导出脚本，用于在开发流程中本地浏览完整早报正文。

## 新增脚本

新增：

```text
scripts/export_rss_markdown.py
```

默认 RSS 源：

```text
https://imjuya.github.io/juya-ai-daily/rss.xml
```

默认输出目录：

```text
temp/rss_exports/
```

该目录已加入 `.gitignore`，避免将导出的第三方全文内容提交到仓库。

## 使用方式

```powershell
python scripts/export_rss_markdown.py
```

脚本会输出生成的 Markdown 文件绝对路径。

也可以指定源和输出目录：

```powershell
python scripts/export_rss_markdown.py --feed-url https://example.com/rss.xml --output-dir temp/rss_exports
```

## 输出内容

Markdown 文件包含：

- 标题
- RSS 源 URL
- 原文链接
- 发布时间
- 条目 ID
- 从 `content_html` 转换得到的完整纯文本正文

## 后续计划

该导出脚本可作为发送前预览工具。下一步可以基于同一份 `content_text` 实现：

- QQ 消息分段
- 发送前预览
- 已发送条目去重
