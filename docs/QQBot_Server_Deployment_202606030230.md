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

## 2026-07-11 实际部署补充

AI 早报微信 / B站双来源版本没有通过 `git pull` 部署，而是使用受控文件清单同步到 `/root/tai/qq-bot`。部署时刻意保留了服务器现有的：

- `.env` 与 `data/`；
- 带状态查询定制的 `app.py`；
- `utils/api_utils.py` 中的私聊发送功能；
- 已有运行数据和投递状态文件。

`utils/api_utils.py` 以远程版本为基础做过三方合并，只加入 OneBot 业务成功判定和重试逻辑。部署前在服务器通过了 36 项单测、Python 编译、固定文章烟测和自动发现烟测，之后重启了 `tai_qqbot`。

因此服务器当前虽然仍显示 Git 提交 `53fed17`，实际运行文件已经包含本地合并提交 `9b61636` 的 AI 早报功能；远程工作树为修改/未跟踪状态。后续不得直接用 `git reset --hard`、整目录覆盖或未经比对的 `git pull` 清理，否则可能丢失服务器专属功能和配置。

下一次部署前应先：

1. 对远程定制文件和本地版本做逐项差异审计；
2. 把仍需要的远程定制纳入正式提交或环境配置；
3. 备份 `.env`、`data/` 和投递状态；
4. 在干净、可追溯的部署树上运行测试和只读烟测；
5. 确认只有一个 `tai_qqbot` 进程后再切换；
6. 为 `run.log` 配置轮转，避免常驻进程无限追加日志。
