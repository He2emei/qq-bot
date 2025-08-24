# Notion-Tools 功能集成说明

## 📋 概述

已成功将 Notion-Tools 文件夹中的核心功能整合到原项目中。主要功能包括：

- 📅 **每日日记管理**：自动创建和管理 Notion 每日日记页面
- 🖼️ **壁纸自动更新**：每日自动更新日记页面封面为 Bing 壁纸
- 🤖 **QQ机器人集成**：通过 QQ 机器人命令管理日记
- ⏰ **定时任务**：自动化的日记创建和封面更新

## 🚀 主要功能

### 1. QQ 机器人命令

| 命令 | 功能描述 |
|------|----------|
| `#daily` | 查看今日日记页面内容 |
| `#add_daily` | 创建今日日记页面 |
| `#update_cover` | 更新今日日记封面为最新 Bing 壁纸 |

### 2. 自动定时任务

- **每日 0:30**：自动创建今日日记页面（带 Bing 壁纸封面）
- **每周日 0:30**：检查是否需要创建下周页面
- **每日 8:00**：更新今日日记封面为最新 Bing 壁纸

### 3. 服务类

- **NotionService**：核心的 Notion API 服务类
- **NotionDailyManager**：每日日记管理器
- **NotionScheduler**：定时任务调度器

## ⚙️ 配置说明

### 1. Notion API 配置

在 `config.py` 中已添加以下配置项：

```python
# Notion API 配置
NOTION_TOKEN = "your_notion_token"          # Notion API Token
NOTION_VERSION = "2022-06-28"               # API 版本

# Notion 数据库配置
NOTION_DATABASES = {
    'daily': '32ace5e970b647e784d4d96ced0b2528',      # Daily Dairy 2.0
    'weekly': 'b933933868254b769bf96e3768b1dbda',    # Weekly Dairy 2.0
    'terms': 'ec2a978cd73e43d49ddf41693e68fc15'     # Terms Dairy 2.0
}

# 代理配置（可选）
NOTION_PROXY = "http://127.0.0.1:10809"  # 设置为空字符串禁用代理
```

### 2. 获取 Notion API Token

1. 访问 [Notion Developers](https://developers.notion.com/)
2. 创建新应用并获取 API Token
3. 分享数据库给你的应用
4. 更新 `config.py` 中的 `NOTION_TOKEN`

### 3. 数据库 ID 获取

1. 打开 Notion 数据库
2. 点击右上角的 "..." 菜单
3. 选择 "Copy link"
4. 从链接中提取数据库 ID（URL 中最后一个 "/" 后的 32 位字符串）

## 📁 文件结构

```
qq_bot/
├── services/
│   ├── notion_service.py          # 核心 Notion API 服务
│   ├── notion_scheduler.py        # 定时任务调度器
│   └── ...
├── handlers/
│   ├── notion_handler.py          # QQ 机器人命令处理
│   └── ...
├── utils/
│   ├── notion_utils.py            # Notion 工具函数
│   └── ...
├── data/
│   └── notion_templates/
│       └── daily_template.json    # 日记页面模板
├── config.py                      # 配置文件
├── requirements.txt               # 依赖包
└── test_notion_integration.py     # 集成测试
```

## 🔧 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置设置

1. 编辑 `config.py`
2. 设置 `NOTION_TOKEN` 为你的 Notion API Token
3. 确保数据库 ID 配置正确
4. 根据需要配置代理

### 3. 测试集成

```bash
python test_notion_integration.py
```

### 4. 运行应用

```bash
python app.py
```

应用启动后会自动开始 Notion 定时任务。

## 🎯 使用方法

### 通过 QQ 机器人使用

1. 在配置的群聊中发送 `#daily` 查看今日日记
2. 发送 `#add_daily` 创建今日日记页面
3. 发送 `#update_cover` 更新封面

### 编程接口使用

```python
from services.notion_service import daily_manager, notion_service

# 创建今日日记页面
result = daily_manager.add_today_page(with_cover=True)

# 获取今日页面
today_page = daily_manager.get_today_page()

# 更新封面
success = daily_manager.update_daily_cover()
```

## 🐛 故障排除

### 常见问题

1. **API 连接失败**
   - 检查 `NOTION_TOKEN` 是否正确
   - 确认数据库已分享给应用
   - 检查网络连接和代理设置

2. **页面创建失败**
   - 验证数据库 ID 是否正确
   - 检查数据库结构是否匹配模板

3. **Bing 图片获取失败**
   - 可能是网络问题，会自动使用默认图片
   - 检查网络连接

### 日志查看

应用运行时会在控制台输出详细的日志信息，帮助诊断问题。

## 🔄 更新说明

- 自动定时任务会在应用启动时开始运行
- QQ 机器人命令会实时响应
- 错误会记录在日志中并尝试恢复

## 📝 待改进功能

- [ ] 增加更多 Notion 数据库操作
- [ ] 支持自定义页面模板
- [ ] 添加更多 QQ 机器人命令
- [ ] 实现周/月报自动化生成
- [ ] 添加数据统计功能

---

如有问题或建议，请检查日志输出或查看相关代码文件。