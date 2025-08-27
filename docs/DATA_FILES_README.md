# 数据文件管理说明

## 概述

本项目中的某些文件包含用户数据、配置信息或运行时生成的内容，这些文件不应该在不同环境之间共享，以避免数据冲突或覆盖。

## 被忽略的文件

以下文件和目录已被添加到 `.gitignore`，不会被 Git 跟踪：

### 数据库文件
- `data/machines.db` - 机器信息数据库
- `data/faq_images/` - FAQ功能下载的图片文件

### 配置文件
- `data/authenticatorList.json` - 身份验证器列表
- `data/code.json` - 代码相关数据
- `data/ze_account.json` - ZE账户信息
- `data/memory.json` - 记忆数据
- `data/yqm.json` - YQM相关数据
- `data/help.json` - 帮助信息

## 使用说明

### 本地开发环境
1. 这些文件在你的本地环境中正常使用
2. 数据库文件会自动创建和更新
3. 图片文件会自动下载到 `data/faq_images/` 目录

### 部署到服务器
1. **不要** 将这些数据文件上传到服务器
2. 服务器会创建自己的空数据库和目录结构
3. 如果需要迁移数据，请手动复制数据库文件

### 数据迁移
如果需要在不同环境之间迁移数据：

```bash
# 导出数据库（如果需要）
sqlite3 data/machines.db .dump > machines_backup.sql

# 在目标环境中导入
sqlite3 data/machines.db < machines_backup.sql
```

## 目录结构

```
data/
├── machines.db          # 机器数据库（已忽略）
├── faq_images/          # FAQ图片目录（已忽略）
│   └── .gitkeep        # 保留空目录结构
├── authenticatorList.json  # 验证器列表（已忽略）
├── code.json           # 代码数据（已忽略）
├── ze_account.json     # ZE账户（已忽略）
├── memory.json         # 记忆数据（已忽略）
├── yqm.json           # YQM数据（已忽略）
└── help.json          # 帮助信息（已忽略）
```

## 注意事项

1. **不要手动删除 `.gitkeep` 文件** - 它确保空目录在 Git 中被保留
2. **不要将数据文件添加到 Git** - 即使是临时添加
3. **定期备份重要数据** - 虽然文件被忽略，但仍然需要备份
4. **服务器部署时注意权限** - 确保应用有读写数据目录的权限

## 故障排除

### 数据库文件丢失
如果 `data/machines.db` 文件丢失，应用会自动重新创建空数据库。

### 图片文件丢失
FAQ 中的图片链接会失效，但可以通过重新编辑 FAQ 条目来恢复图片。

### 权限问题
确保运行应用的账户对 `data/` 目录有读写权限。