# NapCat WebSocket 发送说明 202606030214

## 更新概述

本次将 QQ 消息发送能力扩展为支持 NapCat WebSocket action。

此前 `utils.api_utils` 只支持普通 HTTP action，例如：

```text
GET /send_group_msg
POST /send_group_forward_msg
```

但当前 NapCat 端口是 WebSocket 端口，普通 HTTP 请求会返回：

```text
426 Upgrade Required
```

因此新增 WebSocket action 发送逻辑。

## 配置

`config.py` 新增：

```python
NAPCAT_WS_URL = os.getenv("NAPCAT_WS_URL", "ws://127.0.0.1:23334")
NAPCAT_ACCESS_TOKEN = os.getenv("NAPCAT_ACCESS_TOKEN", "")
```

`.env.example` 新增：

```text
NAPCAT_WS_URL=ws://127.0.0.1:23334
NAPCAT_ACCESS_TOKEN=your_napcat_access_token_here
```

密钥应写入本地 `.env`，不要提交到 Git。

## 实现

`utils/api_utils.py` 新增内部函数：

```python
_napcat_ws_request(action, params, timeout=20)
```

请求格式：

```json
{
  "action": "send_group_msg",
  "params": {},
  "echo": "uuid"
}
```

响应处理：

- 跳过 lifecycle 等非 echo 消息
- 等待同一 `echo` 的 action response
- 仅当 `status == "ok"` 时视为成功

## 影响范围

以下函数会优先使用 WebSocket action：

- `send_group_message(group_id, message)`
- `send_group_forward_message(group_id, messages)`

如果 WebSocket 不可用，会回退到原 HTTP action。

## 验证结果

已验证：

- WebSocket 端口可连接
- `get_status` 返回：

```text
online = True
good = True
```

已按要求将最新 RSS 早报测试推送到：

```text
638227713
```

结果：

- 普通重点消息发送成功
- 群合并转发消息发送成功

## 注意

测试时使用了本地 `.env` 中的 `NAPCAT_ACCESS_TOKEN`。该密钥不写入仓库。

部署到 `tai261.xjtumc.com` 时，QQ Bot 与 NapCat 在同一台服务器上，因此默认使用 `127.0.0.1:23334`。本地开发如果需要访问远程 NapCat，可在本地 `.env` 中覆盖为远程地址。
