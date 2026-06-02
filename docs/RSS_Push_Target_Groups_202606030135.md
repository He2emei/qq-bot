# RSS 推送目标群配置说明 202606030135

## 更新概述

本次更新 RSS 自动推送目标群配置。

## 目标群

自动推送目标改为：

```text
1105591264 AI-xjtu
962289836 AI-sjtu
```

## 配置变更

`config.py` 的 `GROUP_IDS` 新增：

```python
'ai_xjtu': 1105591264,
'ai_sjtu': 962289836
```

RSS 推送配置改为：

```python
RSS_PUSH_GROUPS = {
    GROUP_IDS['ai_xjtu']: 'AI-xjtu',
    GROUP_IDS['ai_sjtu']: 'AI-sjtu',
}
RSS_PUSH_GROUP_IDS = list(RSS_PUSH_GROUPS.keys())
```

其中 `RSS_PUSH_GROUPS` 保留群昵称，`RSS_PUSH_GROUP_IDS` 用于实际自动推送。

## 测试推送

按要求尝试将最新一期 RSS 测试推送到：

```text
638227713
```

测试结果：

- RSS 拉取成功
- 推送逻辑已进入普通消息发送和合并转发发送
- NapCat HTTP 服务不可达，发送失败

端口检测结果：

```text
127.0.0.1:23333 TcpTestSucceeded = False
```

说明当前本机 NapCat HTTP 服务没有监听 `23333` 端口。待 NapCat 启动后，可重新执行同一测试推送。
