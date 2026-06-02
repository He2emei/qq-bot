# QQ Bot 服务器部署说明 202606030230

## 部署位置

RSS 推送功能部署在：

```text
tai261.xjtumc.com
```

项目目录：

```text
/root/tai/qq-bot
```

运行 screen：

```text
tai_qqbot
```

以后更新项目后，默认部署到这台服务器和这个目录。

## NapCat 端点

服务器上 QQ Bot 与 NapCat 在同一台机器，因此部署环境使用本地端点：

```text
NAPCAT_BASE_URL=http://127.0.0.1:23334
NAPCAT_WS_URL=ws://127.0.0.1:23334
```

`NAPCAT_ACCESS_TOKEN` 写入服务器 `.env`，不提交到 Git。

## RSS 推送目标

正式自动推送群：

```text
1105591264 AI-xjtu
962289836 AI-sjtu
```

测试群：

```text
638227713
```

## 部署流程

常用流程：

```bash
ssh tai261.xjtumc.com
cd /root/tai/qq-bot
git fetch origin
git switch codex/rss-feedparser
git pull --ff-only
. venv/bin/activate
python -m pip install -r requirements.txt
screen -S tai_qqbot -X quit
screen -dmS tai_qqbot bash -lc 'cd /root/tai/qq-bot && . venv/bin/activate && venv/bin/python ./app.py >> run.log 2>&1'
```

检查运行状态：

```bash
screen -ls
tail -n 120 /root/tai/qq-bot/run.log
```

## 当前部署状态

首次部署时已将当前 RSS 最新条目标记为已推送，避免把旧的 `2026-06-02` 早报发送到正式群。

状态文件：

```text
/root/tai/qq-bot/data/rss_state.json
```

下一次 RSS 源出现新条目时，调度器会自动推送到正式群。
