# MC社团机器人FAQ功能详细文档

## 概述

FAQ（Frequently Asked Questions）功能是MC社团机器人核心功能之一，允许用户在群聊中快速查询、编辑和管理常见问题解答内容。该功能支持文本和图片内容，提供完整的CRUD（创建、读取、更新、删除）操作，并具备自动图片处理能力。

## 功能特性

### 1. 核心命令
- **查询FAQ**: `#faq <key>` - 根据关键字查询FAQ内容
- **编辑FAQ**: `#faq edit <key> <contents>` - 新增或更新FAQ条目
- **删除FAQ**: `#faq delete <key>` - 删除指定的FAQ条目
- **列出FAQ**: `#faq list` - 显示所有可用的FAQ关键字
- **帮助信息**: `#faq help` - 显示FAQ系统使用帮助

### 2. 内容支持
- **文本内容**: 支持纯文本FAQ内容
- **图片内容**: 支持图片URL和直接发送图片，系统会自动下载并本地化存储
- **混合内容**: 支持文本和图片的混合内容

### 3. 图片处理
- **自动下载**: 检测内容中的图片URL，自动下载到本地存储
- **格式转换**: 将图片URL转换为CQ码格式用于机器人发送
- **去重存储**: 相同URL的图片只下载一次，使用MD5哈希作为文件名
- **多格式支持**: 支持jpg、jpeg、png、gif、bmp、webp格式

## 架构设计

### 1. 核心组件

#### faq_handler.py - FAQ处理器
```python
# 主要函数
def handle_faq_query(event_data)          # 处理查询命令
def handle_faq_edit(event_data)           # 处理编辑命令
def handle_faq_delete(event_data)         # 处理删除命令
def handle_faq_list(event_data)           # 处理列表命令
def handle_faq_command(event_data)        # 主命令路由器
def process_faq_content(content)          # 内容预处理
def convert_content_to_cq(content)        # CQ码转换
```

#### database_manager.py - 数据库管理器
```python
# FAQ相关方法
def get_faq_content(key: str) -> Optional[str]    # 获取FAQ内容
def set_faq_content(key: str, contents: str) -> bool  # 设置FAQ内容
def delete_faq_content(key: str) -> bool          # 删除FAQ内容
def list_all_faq_keys() -> List[str]              # 获取所有key列表
```

#### image_utils.py - 图片管理器
```python
class ImageManager:
    def download_image(url: str) -> Optional[str]     # 下载图片
    def process_content_images(content: str) -> str   # 处理内容中的图片
    def extract_image_urls(content: str) -> List[str] # 提取图片URL
    def cleanup_old_images(days: int = 30)           # 清理旧图片
```

### 2. 数据库设计

#### FAQ表结构
```sql
CREATE TABLE IF NOT EXISTS faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,           -- FAQ关键字，唯一
    contents TEXT NOT NULL,             -- FAQ内容，支持CQ码
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 数据库配置
- 数据库文件: `data/faq.db`
- 图片存储目录: `data/faq_images/`

### 3. 消息处理流程

#### 查询流程
1. 用户发送 `#faq <key>`
2. 解析命令和参数
3. 从数据库查询对应内容
4. 返回格式化的FAQ内容

#### 编辑流程
1. 用户发送 `#faq edit <key> <contents>`
2. 解析key和contents
3. 处理内容中的图片（下载并转换为CQ码）
4. 存储到数据库
5. 返回操作结果

#### 图片处理流程
1. 检测内容中的图片URL
2. 为每个URL生成MD5哈希作为文件名
3. 检查本地是否已存在该图片
4. 如不存在则下载并保存
5. 将URL替换为本地文件CQ码

## API集成

### 机器人框架集成
- 使用NapCat QQ机器人框架
- 命令注册在 `app.py` 的命令路由表中
- 支持所有配置的群聊使用

### 配置要求
```python
# config.py
NAPCAT_BASE_URL = "http://127.0.0.1:23333"  # NapCat服务地址
FAQ_DATABASE_PATH = 'data/faq.db'           # FAQ数据库路径
FAQ_IMAGES_DIR = 'data/faq_images/'         # 图片存储目录
MONITORED_GROUPS = set(GROUP_IDS.values())  # 监控的群聊列表
```

## 使用示例

### 基本查询
```
用户: #faq server_rules
机器人: 📖 FAQ [server_rules]:

服务器规则：
1. 禁止破坏他人建筑
2. 保持友好聊天环境
3. 举报违规行为请联系管理员
```

### 带图片的编辑
```
用户: #faq edit map_location 服务器地图位置：[图片URL或直接发送图片]
机器人: ✅ FAQ条目 [map_location] 已更新
🖼️ 图片已下载并保存到本地
```

### 列出所有FAQ
```
用户: #faq list
机器人: 📚 FAQ 条目列表:

1. server_rules
2. map_location
3. join_guide
4. commands

共 4 个FAQ条目
💡 使用 #faq <key> 查看具体内容
```

## 错误处理

### 常见错误场景
1. **无效命令格式**: 返回格式提示
2. **key不存在**: 提示未找到指定条目
3. **权限不足**: 显示权限错误信息
4. **网络异常**: 下载图片失败时的降级处理
5. **数据库错误**: 详细的错误日志记录

### 用户友好的反馈
- 所有操作都有明确的成功/失败反馈
- 提供详细的帮助信息
- 支持中英文混合显示

## 扩展性设计

### 1. 权限管理
当前版本所有群成员均可使用，可扩展为：
- 管理员专用编辑权限
- 不同群聊的独立FAQ库
- 用户角色权限控制

### 2. 内容增强
- 支持富文本格式（Markdown）
- 自动分类和标签系统
- 搜索功能扩展
- 统计和使用频率分析

### 3. 性能优化
- 图片CDN加速
- 数据库查询缓存
- 批量操作支持
- 异步图片处理

## 部署和维护

### 文件结构
```
mc_bot/
├── handlers/
│   └── faq_handler.py          # FAQ处理器
├── services/
│   └── database_manager.py     # 数据库管理
├── utils/
│   ├── image_utils.py          # 图片处理
│   └── api_utils.py            # API工具
├── data/
│   ├── faq.db                  # FAQ数据库
│   └── faq_images/             # 图片存储
├── config.py                   # 配置文件
└── app.py                      # 主应用
```

### 维护任务
1. **定期清理**: 运行图片清理任务删除过期图片
2. **备份策略**: 定期备份FAQ数据库
3. **监控日志**: 查看操作日志和错误信息
4. **容量管理**: 监控存储空间使用情况

## 技术栈

- **编程语言**: Python 3.x
- **数据库**: SQLite 3
- **HTTP客户端**: requests
- **图片处理**: Pillow (间接通过CQ码)
- **机器人框架**: NapCat QQ机器人
- **编码格式**: UTF-8

## 总结

MC社团机器人FAQ功能是一个功能完整、易于使用的问答系统，具有以下优势：

1. **易用性**: 简洁的命令格式，清晰的帮助信息
2. **灵活性**: 支持文本和图片混合内容
3. **可靠性**: 完善的错误处理和数据持久化
4. **扩展性**: 模块化设计，易于功能扩展
5. **维护性**: 清晰的代码结构和详细的文档

该功能完全满足MC社团日常问答管理需求，为群成员提供高效的信息查询服务。