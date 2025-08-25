# QQ机器人项目配置指南

## 📋 项目概述

这是一个集成了QBot功能和Notion API的QQ机器人项目，支持游戏管理、验证码生成、Notion数据库查询等功能。

## 🛠️ 系统要求

- **Python版本**: 3.7+
- **操作系统**: Windows 10+, Linux, macOS
- **网络**: 需要访问互联网（用于Notion API调用）

## 📦 安装步骤

### 1. 获取项目代码

```bash
git clone <repository_url>
cd qq_bot
```

### 2. 创建Python虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. 安装项目依赖

```bash
pip install -r requirements.txt
```

## ⚙️ 配置步骤

### 1. 初始化敏感配置

运行配置初始化脚本：

```bash
python init_configs.py
```

此脚本将创建以下敏感配置文件模板：
- `data/authenticatorList.json` - 验证器列表
- `data/code.json` - 验证码映射
- `data/ze_account.json` - ZE账户信息
- `data/memory.json` - AI对话记忆
- `data/yqm.json` - 邀请码列表

### 2. 配置环境变量

1. 复制环境变量模板文件：
```bash
copy .env.example .env
```

2. 编辑 `.env` 文件，填入您的实际值：
```bash
# Notion API 配置
NOTION_TOKEN=your_actual_notion_token_here
NOTION_TOKEN_DIARY=your_actual_notion_diary_token_here
```

### 3. 配置Notion集成

编辑 `config.py` 文件中的Notion相关配置：

```python
# === Notion 配置 ===
# Notion API 配置
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "your_notion_token_here")  # 用于机器、地域和产物查询
NOTION_TOKEN_DIARY = os.getenv("NOTION_TOKEN_DIARY", "your_notion_diary_token_here")  # 用于日记相关操作
NOTION_VERSION = "2022-06-28"
```

#### 获取Notion Token

1. 访问 [Notion Developers](https://developers.notion.com/)
2. 创建新集成或使用现有集成
3. 复制Integration Token
4. 将token填入上述配置文件

### 4. 配置QQ机器人

#### NapCat框架配置

确保NapCat QQ机器人框架已正确安装并运行在：
```
http://127.0.0.1:23333
```

#### QQ群配置

在 `config.py` 中根据需要修改群号配置：

```python
# QQ群号配置
GROUP_IDS = {
    'default': 1011696295,  # 默认群
    'yqm': 176518586,       # 邀请码群
    'game': 491372741,      # 游戏群
    'gl': 767712912,        # 管理群
    'me': 1022453604,       # 个人群
    'jjl_test': 948937168,  # 竞技场测试群
    'jjl': 1042637919,      # 竞技场群
    'another_group': 107013467,  # 其他群
}
```

### 5. 配置外部服务（可选）

根据需要修改 `config.py` 中的外部服务URL：

```python
# 外部服务URL
JJL_BASE_URL = 'http://yunma.xyq5.top/'
JJL_QUERY_URL = JJL_BASE_URL + 'api/api_query'
DYNAMIC_CODE_URL = 'http://47.115.143.149:99/'

# OpenAI / 腾讯知识引擎 API 配置
OPENAI_API_KEY = "your_openai_api_key"  # 替换为您的API Key
OPENAI_BASE_URL = "https://api.lkeap.cloud.tencent.com/v1"
```

### 6. 配置Flask服务

根据需要修改Flask服务配置：

```python
# Flask 服务配置
SERVER_HOST = '0.0.0.0'  # 监听地址
SERVER_PORT = 7779       # 监听端口
```

## 📁 文件权限设置

确保敏感配置文件具有正确的权限：

```bash
# Windows
# 右键文件 -> 属性 -> 安全 -> 限制访问

# Linux/macOS
chmod 600 data/authenticatorList.json
chmod 600 data/code.json
chmod 600 data/ze_account.json
chmod 600 .env
```

## 🚀 启动服务

### 1. 启动主服务

```bash
python app.py
```

服务将在 `http://0.0.0.0:7779` 启动。

### 2. 验证服务状态

访问以下端点验证服务是否正常运行：
- `http://localhost:7779/` - 服务首页

## 🧪 测试配置

### 1. 运行Notion集成测试

```bash
python test_notion_integration.py
```

### 2. 运行机器数据库测试

```bash
python test_machine_debug.py
```

### 3. 查看配置状态

```bash
python init_configs.py status
```

## 📊 监控和日志

### 查看日志

项目会生成运行日志，请检查终端输出或日志文件中的错误信息。

### 常见问题排查

1. **Notion API连接失败**
   - 检查NOTION_TOKEN是否正确配置
   - 验证Notion数据库ID是否正确
   - 检查网络连接和代理设置

2. **QQ机器人连接失败**
   - 确认NapCat服务正在运行
   - 检查NAPCAT_BASE_URL配置
   - 验证QQ群号配置

3. **依赖安装失败**
   - 确认Python版本 >= 3.7
   - 检查pip是否为最新版本
   - 尝试使用国内镜像源

## 🔒 安全建议

1. **定期备份敏感配置**
   ```bash
   python init_configs.py backup
   ```

2. **不要提交敏感文件到Git**
   - 确保 `.env` 文件在 `.gitignore` 中
   - 敏感配置文件已自动加入 `.gitignore`

3. **使用强密码和Token**
   - 定期更新API Token
   - 使用环境变量存储敏感信息

## 📞 技术支持

如果配置过程中遇到问题，请：

1. 检查项目文档：`README_QBot_Integration.md`
2. 查看Notion集成文档：`README_Notion_Integration.md`
3. 查看代理配置指南：`PROXY_GUIDE.md`
4. 查看机器数据库文档：`README_Machine_Database.md`

## 📝 版本信息

- **当前版本**: v1.0.0
- **最后更新**: 2024年8月23日
- **Python版本**: 3.7+
- **主要依赖**: Flask, OpenAI, APScheduler, pyotp

---

**配置完成！** 按照上述步骤操作后，您的QQ机器人项目应该可以在新机器上正常运行。