# QBot 功能整合说明

## 📋 概述

QBot 功能已成功整合到当前项目中，所有核心功能都已迁移并优化。项目现在支持：

### ✅ 已集成功能

#### 1. **AQL 验证器功能**
- `.aql <账户>` - 获取验证码
- `.aqladd <账户> <密钥>` - 添加验证器
- `#aql <账户>` - 获取验证码（群组）
- `#aqladd <账户> <密钥>` - 添加验证器（群组）

#### 2. **游戏管理功能**
- `#游戏列表` - 显示游戏列表
- `#添加游戏 <游戏名>` - 添加游戏
- `#删除游戏 <游戏名>` - 删除游戏
- `#玩什么` - 随机选择游戏
- `#wdlst` - 显示问答列表
- `#wdadd <内容>` - 添加问答
- `#wddel <内容>` - 删除问答
- `#wdhow` - 随机问答
- `#mclst` - 显示MC列表
- `#mcadd <内容>` - 添加MC内容
- `#mcdel <内容>` - 删除MC内容
- `#mchow` - 随机MC内容

#### 3. **@ 功能（新增）**
- `#at <昵称>` - @指定昵称的人
- `#atadd <昵称> <QQ号1> [QQ号2] ...` - 添加昵称
- `#atls` - 显示所有昵称
- `#atdel <昵称> [QQ号]` - 删除昵称或特定QQ

#### 4. **Notion 功能**
- `#daily` - 查看今日日记内容
- `#add_daily` - 创建今日日记页面
- `#update_cover` - 更新今日日记封面为Bing壁纸

#### 5. **机器数据库管理（新增）**
- `#machine_search <产物>` - 根据产物查询生产机器
- `#machine_region <地域>` - 根据地域查询所有机器
- `#machine_regions` - 列出所有可用地域
- `#machine_products` - 列出所有可生产产物
- `#machine_detail <机器名>` - 获取机器详细信息

#### 6. **帮助功能**
- `#help` - 显示帮助信息

## 🔧 配置管理

### 敏感配置文件管理

项目使用专门的配置文件管理系统来避免git冲突：

#### 敏感配置文件（不提交到git）：
- `data/authenticatorList.json` - 验证器列表
- `data/code.json` - 验证码映射
- `data/ze_account.json` - ZE账户信息
- `data/memory.json` - AI对话记忆
- `data/yqm.json` - 邀请码列表

#### 普通配置文件（可提交到git）：
- `data/gameList.json` - 游戏列表
- `data/help.json` - 帮助信息
- `data/mc.json` - MC内容
- `data/wd.json` - 问答内容
- `data/at.json` - @功能配置

### 初始化敏感配置

运行以下命令来初始化敏感配置文件：

```bash
python init_configs.py
```

此命令将：
1. 创建所有必要的配置文件模板
2. 设置正确的目录结构
3. 提供配置说明

### 备份配置

```bash
python init_configs.py backup
```

### 查看配置状态

```bash
python init_configs.py status
```

## 📁 项目结构

```
qq_bot/
├── app.py                      # 主应用文件
├── config.py                  # 主配置文件
├── config_manager.py          # 配置管理器
├── init_configs.py            # 配置初始化脚本
├── .gitignore                 # Git忽略文件
├── requirements.txt           # Python依赖
├── README_QBot_Integration.md # 本说明文档
├── handlers/                  # 命令处理器
│   ├── aql_handler.py        # AQL验证器处理器
│   ├── game_handler.py       # 游戏管理处理器
│   ├── at_handler.py         # @功能处理器
│   └── notion_handler.py     # Notion处理器
├── services/                  # 后台服务
│   ├── notion_service.py     # Notion API服务
│   ├── notion_scheduler.py   # Notion定时任务
│   ├── totp_generator.py     # TOTP生成器
│   └── process_yqm.py        # 邀请码处理
├── utils/                     # 工具模块
│   ├── api_utils.py          # API工具
│   └── file_utils.py         # 文件工具
└── data/                      # 数据文件
    ├── notion_templates/      # Notion模板
    ├── gameList.json          # 游戏列表
    ├── help.json              # 帮助信息
    ├── at.json                # @功能配置
    └── [敏感配置文件]         # 不提交到git
```

## 🚀 部署说明

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化敏感配置
python init_configs.py
```

### 2. 配置敏感信息

编辑以下文件，填入您的敏感信息：

- `data/authenticatorList.json` - 添加您的验证器
- `data/code.json` - 添加验证码映射
- `data/ze_account.json` - 添加ZE账户
- `config.py` - 修改Notion配置

### 3. 启动服务

```bash
python app.py
```

## ⚠️ 重要提醒

### 安全注意事项

1. **敏感配置保护**：
   - 敏感配置文件已加入`.gitignore`
   - 部署到服务器时请手动配置这些文件
   - 定期备份敏感配置

2. **Git 管理**：
   - 不要强制提交敏感文件
   - 使用`git status`检查是否有敏感文件被跟踪
   - 如有误提交，使用以下命令移除：
   ```bash
   git rm --cached data/authenticatorList.json
   git rm --cached data/code.json
   # ... 其他敏感文件
   ```

3. **服务器部署**：
   - 在服务器上重新运行`python init_configs.py`
   - 手动配置所有敏感信息
   - 设置适当的文件权限

### 功能测试

运行测试脚本验证功能：

```bash
python test_notion_integration.py
```

## 📞 支持与反馈

如果您在使用过程中遇到问题，请：

1. 检查日志文件
2. 验证配置文件格式
3. 确认网络连接正常
4. 查看项目文档

## 📝 更新日志

### v1.0.0 (当前版本)
- ✅ 完整迁移QBot所有核心功能
- ✅ 实现配置管理系统避免git冲突
- ✅ 优化代码结构和错误处理
- ✅ 添加详细的文档说明
- ✅ 新增机器数据库管理功能
- ✅ 集成Notion API进行数据库查询
- ✅ 支持QQ群聊管理Notion数据库

---

**最后更新时间**: 2024年8月23日