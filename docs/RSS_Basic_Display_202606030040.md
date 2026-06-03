# RSS 基础展示说明 202606030040

## 更新概述

本次新增 RSS 早报的基础展示流程。

展示分为两条 QQ 消息：

1. 普通群消息
   - 只发送重点新闻标题
   - 不包含具体正文

2. 群合并转发消息
   - 第一条节点提供原作者信息
   - 后续每个节点对应一个新闻类别
   - `要闻` 类别也进入合并转发
   - 关键词命中的重点新闻仍保留在原类别中
   - 保留新闻链接

## 新增配置

`config.py` 新增：

```python
RSS_FEED_URL = 'https://imjuya.github.io/juya-ai-daily/rss.xml'
RSS_SOURCE_NAME = '橘鸦AI早报'
RSS_SOURCE_URL = 'https://imjuya.github.io/juya-ai-daily/'
```

## 新增发送工具

`utils/api_utils.py` 新增：

```python
send_group_forward_message(group_id, messages)
```

该方法调用 NapCat：

```text
POST /send_group_forward_msg
```

用于发送自定义节点合并转发消息。

## 新增展示服务

新增：

```text
services/rss_display_service.py
```

主要函数：

- `format_important_news_message(result)`
  - 构建普通群消息
  - 格式示例：

```text
今天是2026年06月02日，星期二，为您带来今日AI早报：
1. 千问发布多模态智能体模型 Qwen3.7-Plus
2. MiniMax Token Plan 切换至 Token 计费并补偿老用户
```

- `build_other_news_forward_nodes(result, bot_user_id, bot_nickname=None)`
  - 构建合并转发自定义节点
  - 第一条节点包含：
    - RSS 来源
    - 原文链接
    - 哔哩哔哩视频版链接
    - 作者主页
    - 关注原作者提示
  - 后续节点按类别展示新闻标题和链接

## 新增 QBot 指令

新增：

```text
#rssdaily
```

触发后：

1. 获取最新 RSS 条目
2. 执行重点信息筛选
3. 发送重点新闻普通消息
4. 发送其他类别合并转发消息

## 验证情况

使用最新一期 RSS 做本地预览：

- 普通重点消息包含 7 条重点新闻
- 合并转发节点共 8 个
  - 1 个来源信息节点
  - 7 个类别节点
- `要闻` 类别进入合并转发，并保留新闻链接
- 被关键词标记为重点的新闻仍保留在原类别节点中

已执行：

```powershell
python -m unittest tests.unit.test_rss_service tests.unit.test_rss_filter_service tests.unit.test_rss_display_service
python -m compileall -q app.py handlers\rss_handler.py services\rss_display_service.py services\rss_filter_service.py utils\api_utils.py tests\unit\test_rss_display_service.py
```

结果均通过。

## 注意

本次只做本地格式预览和接口代码接入，未实际连接 NapCat 发送 QQ 消息。
