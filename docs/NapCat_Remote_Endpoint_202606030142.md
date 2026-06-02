# NapCat 远程端点配置说明 202606030142

## 更新概述

本次更新 NapCat HTTP 服务地址。

## 配置变更

`config.py` 中：

```python
NAPCAT_BASE_URL = "http://tai261.xjtumc.com:23334"
```

该端点说明：

- 主机：`tai261.xjtumc.com`
- 端口：`23334`
- 用户说明该端口会长期保持开启

## 影响范围

所有通过 `utils.api_utils` 发送的 QQ 消息都会使用该端点：

- 普通群消息：`/send_group_msg`
- 群合并转发消息：`/send_group_forward_msg`

RSS 早报测试推送和自动推送也会使用该端点。
