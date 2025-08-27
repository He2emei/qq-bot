# 机器数据库本地化迁移完成

## 迁移概述

已成功将原来依赖Notion API实现的机器查询功能迁移到本地SQLite数据库，同时保留了Notion相关的日记功能。

### 🎯 重要改进
- **支持重复名称机器**：通过复合唯一约束(name, region, coordinates)，允许同名机器（如两个"刷雪机"）在不同地域或坐标下共存
- **完整数据保留**：成功导入77台机器，12个地域，159种产物，无数据丢失

## 主要变化

### ✅ 已完成的迁移

1. **创建SQLite数据库** (`services/database_manager.py`)
   - 设计了完整的数据库表结构
   - 包含machines、products、regions、maintainers表
   - 支持多对多关系查询
   - **复合唯一约束**：`UNIQUE(name, region, coordinates)` 支持重复名称机器

2. **数据导入工具** (`import_machine_data.py`)
   - 从CSV文件自动导入机器数据
   - 成功导入12个地域，159种产物，77台机器
   - 支持重复名称机器（如两个"刷雪机"）
   - 自动处理产物和地域的关联关系

3. **机器管理器重构** (`services/machine_manager.py`)
   - 完全重写查询方法使用本地数据库
   - 保持与原有API接口兼容
   - 保留增删改功能（标记为暂未实现）

4. **功能验证**
   - 机器查询功能测试通过
   - 日记功能保持完整（使用Notion API）
   - 所有原有命令继续可用

### 📁 新增文件

- `services/database_manager.py` - 本地数据库管理器
- `import_machine_data.py` - 数据导入脚本
- `test_machine_query.py` - 机器查询功能测试
- `test_fixed_queries.py` - 修复后查询功能测试
- `test_duplicate_machines.py` - 重复名称机器测试
- `test_diary_function.py` - 日记功能测试
- `data/machines.db` - SQLite数据库文件

## 使用方法

### 1. 数据库初始化

```bash
# 导入机器数据（首次运行）
python import_machine_data.py

# 测试重复名称机器功能
python test_duplicate_machines.py

# 测试修复后的查询功能
python test_fixed_queries.py
```

### 2. 机器查询命令

所有原有命令继续可用：

- `#machine_search <产物名称>` - 根据产物查询机器
- `#machine_region <地域名称>` - 根据地域查询机器
- `#machine_detail <机器名称>` - 获取机器详细信息
- `#machine_regions` - 列出所有地域
- `#machine_products` - 列出所有产物

### 3. 日记功能

日记相关功能完全不受影响：

- `#daily` - 查看今日日记
- `#add_daily` - 创建今日日记
- `#update_cover` - 更新日记封面

## 重复名称机器支持

### 🎯 核心特性
- **复合唯一约束**：`UNIQUE(name, region, coordinates)`
- **智能区分**：同名机器通过地域和坐标自动区分
- **完整保留**：CSV中的所有重复记录都会被导入

### 📋 示例场景
```sql
-- 两个"刷雪机"可同时存在：
INSERT INTO machines (name, region, coordinates) VALUES
('刷雪机', '樱岭', '-3191 68 8620'),
('刷雪机', '思源市', '245 64 2907');
```

### 🔍 查询行为
- **按产物查询**：`#machine_search 雪块` → 返回2台刷雪机
- **按地域查询**：`#machine_region 樱岭` → 返回樱岭的刷雪机
- **详细信息**：每个机器通过地域+坐标唯一标识

## 性能优势

- **查询速度**：本地数据库查询比Notion API快数倍
- **离线可用**：无需网络连接即可查询机器数据
- **稳定性**：不受Notion API限制和网络问题影响
- **数据安全**：敏感数据存储在本地
- **完整性**：支持所有CSV数据，无信息丢失

## 技术细节

### 数据库结构

```sql
-- 机器表（支持重复名称，通过复合约束区分）
CREATE TABLE machines (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT,
    dimension TEXT,
    coordinates TEXT,
    UNIQUE(name, region, coordinates)  -- 复合唯一约束
);

-- 产物表
CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT UNIQUE);

-- 地域表
CREATE TABLE regions (id INTEGER PRIMARY KEY, name TEXT UNIQUE);

-- 多对多关联表
CREATE TABLE machine_products (machine_id, product_id, FOREIGN KEY...);
CREATE TABLE machine_maintainers (machine_id, maintainer_id, FOREIGN KEY...);
```

### 兼容性

- 完全保持原有API接口
- handlers/notion_handler.py 无需修改
- 所有现有命令继续工作

## 注意事项

1. **重复名称机器**：系统支持同名机器，通过地域+坐标自动区分
2. **数据更新**：如需添加新机器，请直接更新数据库或重新导入CSV文件
3. **备份**：重要数据请定期备份 `data/machines.db`
4. **权限**：确保数据库文件具有适当的读写权限
5. **数据完整性**：复合约束确保不会意外覆盖重要数据

## 测试结果

```
地域数量: 12
产物数量: 159
机器数量: 77
'雪块' 相关机器数量: 2  (支持重复名称机器)
'骨粉' 相关机器数量: 3
'铁锭' 相关机器数量: 2
```

### 重复名称机器示例
- **樱岭刷雪机**: 坐标 (-3191, 68, 8620)
- **思源市刷雪机**: 坐标 (245, 64, 2907)

迁移成功完成！🎉