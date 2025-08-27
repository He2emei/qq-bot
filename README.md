# QQ机器人项目 - 综合帮助文档

## 📋 项目概述

这是一个功能全面的QQ机器人项目，集成了多种实用功能，包括游戏管理、验证码生成、Notion数据库查询、FAQ系统等。项目采用Flask框架构建，支持QQ群聊交互，通过NapCat QQ机器人框架实现消息处理。

## 🏗️ 项目架构

### 核心组件

#### 1. **主应用层** (`app.py`)
- Flask Web服务器
- QQ消息路由和分发
- 命令解析和处理器调用

#### 2. **配置管理** (`config.py`)
- 全局配置管理
- Notion API配置
- QQ群配置
- 数据库路径配置

#### 3. **服务层** (`services/`)
- **database_manager.py**: 本地SQLite数据库管理器
- **machine_manager.py**: 机器数据库查询服务
- **notion_service.py**: Notion API集成服务

#### 4. **处理器层** (`handlers/`)
- **notion_handler.py**: Notion相关命令处理
- **aql_handler.py**: AQL验证码处理
- **game_handler.py**: 游戏管理处理
- **at_handler.py**: @功能处理
- **faq_handler.py**: FAQ系统处理

#### 5. **工具层** (`utils/`)
- **api_utils.py**: API调用工具
- **notion_utils.py**: Notion工具函数
- **file_utils.py**: 文件操作工具
- **image_utils.py**: 图片处理工具

## 🚀 主要功能

### 1. **AQL验证器功能**
- `.aql <账户>` / `#aql <账户>` - 获取验证码
- `.aqladd <账户> <密钥>` / `#aqladd <账户> <密钥>` - 添加验证器

### 2. **游戏管理功能**
- `#游戏列表` - 显示游戏列表
- `#添加游戏 <游戏名>` - 添加游戏
- `#删除游戏 <游戏名>` - 删除游戏
- `#玩什么` - 随机选择游戏
- `#wdlst` / `#wdadd <内容>` / `#wddel <内容>` / `#wdhow` - 问答管理
- `#mclst` / `#mcadd <内容>` / `#mcdel <内容>` / `#mchow` - MC内容管理

### 3. **@功能**
- `#at <昵称>` - @指定昵称的人
- `#atadd <昵称> <QQ号1> [QQ号2] ...` - 添加昵称
- `#atls` - 显示所有昵称
- `#atdel <昵称> [QQ号]` - 删除昵称或特定QQ

### 4. **Notion集成功能**

#### 日记管理
- `#daily` - 查看今日日记内容
- `#add_daily` - 创建今日日记页面
- `#update_cover` - 更新今日日记封面为Bing壁纸

#### 机器数据库查询
- `#machine_search <产物>` - 根据产物查询生产机器
- `#machine_region <地域>` - 根据地域查询所有机器
- `#machine_regions` - 列出所有可用地域
- `#machine_products` - 列出所有可生产产物
- `#machine_detail <机器名>` - 获取机器详细信息

### 5. **FAQ系统**
- `#faq` - 显示FAQ列表
- `#faq <关键词>` - 查询特定FAQ
- `#faq edit <关键词>` - 编辑FAQ条目

## 📊 数据存储架构

### 本地SQLite数据库 (`data/machines.db`)

#### 核心表结构
- **machines**: 机器基本信息（支持重复名称，通过复合约束区分）
- **products**: 产物信息
- **regions**: 地域信息
- **machine_products**: 机器-产物关联表（多对多）
- **maintainers**: 维护者信息
- **machine_maintainers**: 机器-维护者关联表（多对多）
- **faq**: FAQ内容表

#### 设计特点
- 支持同名机器通过地域+坐标唯一区分
- 完整的多对多关系支持
- 本地化存储，无网络依赖
- 高性能查询

### 配置文件存储
- `data/authenticatorList.json` - 验证器列表
- `data/code.json` - 验证码映射
- `data/ze_account.json` - ZE账户信息
- `data/memory.json` - AI对话记忆
- `data/yqm.json` - 邀请码列表
- `data/gameList.json` - 游戏列表
- `data/help.json` - 帮助信息
- `data/wd.json` - 问答内容
- `data/mc.json` - MC内容
- `data/at.json` - @功能配置

## ⚙️ 安装和配置

### 环境要求
- Python 3.7+
- Windows 10+, Linux, macOS
- 互联网连接（用于Notion API调用）

### 快速开始

1. **克隆项目**
   ```bash
   git clone <repository_url>
   cd qq_bot
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **初始化配置**
   ```bash
   python init_configs.py
   ```

5. **配置环境变量**
   - 复制 `.env.example` 到 `.env`
   - 填入Notion API Token等敏感信息

6. **导入机器数据**
   ```bash
   python import_machine_data.py
   ```

7. **启动服务**
   ```bash
   python app.py
   ```

## 🔧 高级配置

### Notion集成配置

1. **获取API Token**
   - 访问 [Notion Developers](https://developers.notion.com/)
   - 创建集成并获取Token
   - 分享数据库给集成

2. **数据库配置**
   - machines: 机器数据库
   - products: 产物数据库
   - regions: 地域数据库
   - daily/weekly/terms: 日记数据库

### QQ机器人配置

1. **NapCat框架**
   - 确保NapCat运行在 `http://127.0.0.1:23333`

2. **群权限配置**
   - 在 `config.py` 中配置监控的群号

### 代理配置

如遇到网络问题，可配置代理：
```python
NOTION_PROXY = "http://127.0.0.1:7890"  # 或其他代理地址
```

## 📖 详细文档

项目详细文档已整理在 `docs/` 文件夹中：

- [**CONFIGURATION_GUIDE.md**](docs/CONFIGURATION_GUIDE.md) - 完整配置指南
- [**README_Machine_Database.md**](docs/README_Machine_Database.md) - 机器数据库使用说明
- [**README_Notion_Integration.md**](docs/README_Notion_Integration.md) - Notion集成说明
- [**README_QBot_Integration.md**](docs/README_QBot_Integration.md) - QBot功能说明
- [**README_Machine_Database_Migration.md**](docs/README_Machine_Database_Migration.md) - 数据库迁移说明
- [**README_Relation_Integration.md**](docs/README_Relation_Integration.md) - Relation功能说明
- [**PROXY_GUIDE.md**](docs/PROXY_GUIDE.md) - 代理配置指南
- [**DATA_FILES_README.md**](docs/DATA_FILES_README.md) - 数据文件管理说明

## 🧪 测试和验证

### 功能测试
```bash
# Notion集成测试
python tests/test_notion_integration.py

# 机器数据库测试
python tests/test_machine_debug.py

# 关系功能测试
python tests/test_relation_functionality.py

# FAQ功能测试
python tests/test_faq.py
```

### 命令测试
在QQ群中发送命令进行测试：
```
#machine_regions
#machine_search 铁锭
#daily
#help
```

## 📋 项目管理和Todolist功能

### Todolist使用说明

项目支持内置的**任务清单管理功能**，可以帮助开发者或用户跟踪任务进度：

#### 功能特点
- ✅ **结构化任务跟踪**：支持多步骤任务的有序管理
- ✅ **实时状态更新**：任务状态实时反映在environment_details中
- ✅ **易于编辑**：支持动态添加、修改、删除任务
- ✅ **状态管理**：三种状态（待完成、进行中、已完成）

#### 使用方法

1. **创建Todolist**
   ```xml
   <update_todo_list>
   <todos>
   [ ] 任务描述1
   [ ] 任务描述2
   [-] 正在进行的任务
   [x] 已完成的任务
   </todos>
   </update_todo_list>
   ```

2. **状态标识说明**
   - `[ ]` - 待完成任务
   - `[-]` - 正在进行中的任务
   - `[x]` - 已完成任务

3. **更新任务状态**
   - 任务完成后，通过 `update_todo_list` 工具更新状态
   - 可以同时更新多个任务的状态

#### 示例场景
- 项目开发阶段跟踪功能实现进度
- 部署时检查配置步骤完成情况
- 维护时记录修复任务状态

### 测试文件组织

所有测试代码已统一整理到 `tests/` 文件夹中：

#### 测试文件列表
- **Notion相关测试**: `test_notion_integration.py`, `debug_notion.py`
- **机器数据库测试**: `test_machine_debug.py`, `test_machine_query.py`, `test_duplicate_machines.py`
- **FAQ系统测试**: `test_faq.py`, `test_faq_images.py`
- **数据库测试**: `test_database.py`, `test_fixed_queries.py`
- **其他功能测试**: `test_command.py`, `test_diary_function.py`, `test_relation_functionality.py`
- **调试工具**: `detailed_test.py`, `simple_debug.py`, `find_database_id.py`

#### 运行测试
```bash
# 进入测试目录
cd tests

# 运行特定测试
python test_notion_integration.py
python test_machine_debug.py
```

## 🛠️ 开发和扩展

### 添加新功能

1. **创建处理器**
   ```python
   # handlers/new_handler.py
   def handle_new_command(event_data):
       # 处理逻辑
       pass
   ```

2. **注册命令路由**
   ```python
   # app.py
   COMMAND_ROUTER = {
       '#new_command': new_handler.handle_new_command,
       # ...
   }
   ```

3. **添加配置**
   ```python
   # config.py
   NEW_CONFIG = "value"
   ```

### 数据库扩展

1. **添加新表**
   ```python
   # services/database_manager.py
   cursor.execute('''
       CREATE TABLE IF NOT EXISTS new_table (
           id INTEGER PRIMARY KEY,
           name TEXT NOT NULL
       )
   ''')
   ```

2. **添加查询方法**
   ```python
   def get_new_data(self, param: str) -> List[Dict[str, Any]]:
       # 查询逻辑
       pass
   ```

## 🔒 安全和权限

### 数据安全
- 敏感配置文件自动加入 `.gitignore`
- 支持数据备份和恢复
- 本地化存储减少数据泄露风险

### 权限管理
- QQ群白名单机制
- Notion集成权限控制
- 文件系统权限设置

## 📊 性能优化

### 查询优化
- 本地数据库查询速度快
- 异步消息处理
- 缓存机制
- 分页发送长消息

### 网络优化
- 重试机制
- 超时控制
- 代理支持

## 🎯 版本信息

- **当前版本**: v1.0.0
- **最后更新**: 2024年8月27日
- **Python版本**: 3.7+
- **主要依赖**: Flask, requests, sqlite3, APScheduler

## 📞 支持与反馈

### 常见问题

1. **Notion API连接失败**
   - 检查Token配置
   - 验证数据库权限
   - 查看代理设置

2. **数据库查询无结果**
   - 确认数据已正确导入
   - 检查查询参数格式
   - 验证数据库文件存在

3. **QQ消息无响应**
   - 确认NapCat服务运行
   - 检查群号配置
   - 查看应用日志

### 获取帮助

1. 查看详细文档（`docs/`文件夹）
2. 检查应用运行日志
3. 验证配置文件格式
4. 确认网络连接正常

---

**项目状态**: ✅ 功能完整，文档齐全，可投入使用

*如有问题或建议，请查看详细文档或检查日志输出。*