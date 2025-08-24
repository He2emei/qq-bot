# Notion API 代理设置指南

## 🚀 快速解决方案

如果您遇到 400 错误或连接问题，请按以下步骤操作：

### 1. **禁用代理（推荐）**

最简单的解决方案是完全禁用代理：

```python
# 在 config.py 中设置
NOTION_PROXY = ""  # 空字符串表示禁用代理
```

然后重启您的应用：
```bash
python app.py
```

### 2. **使用正确的代理格式**

如果您必须使用代理，请确保格式正确：

```python
# 在 config.py 中设置
NOTION_PROXY = "http://127.0.0.1:7890"  # HTTP代理
# 或者
NOTION_PROXY = "https://127.0.0.1:7890" # HTTPS代理
```

### 3. **验证代理配置**

运行以下命令测试代理：

```bash
# 测试代理连接
python -c "
import requests
try:
    response = requests.get('https://api.notion.com/v1/users/me', proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}, timeout=10)
    print(f'Proxy Status: {response.status_code}')
except Exception as e:
    print(f'Proxy Error: {e}')
"
```

## 🔧 详细代理配置

### 代理服务器要求

1. **支持 HTTPS**: 代理必须支持 HTTPS 连接
2. **稳定连接**: 代理服务器必须稳定运行
3. **无认证要求**: 目前配置不支持代理认证

### 常见代理工具

#### 1. Clash
- 默认端口: 7890
- 配置: `NOTION_PROXY = "http://127.0.0.1:7890"`

#### 2. V2Ray
- 通常使用端口: 1080 或 1081
- 配置: `NOTION_PROXY = "http://127.0.0.1:1080"`

#### 3. Shadowsocks
- 通常使用端口: 1080
- 配置: `NOTION_PROXY = "http://127.0.0.1:1080"`

### 代理配置验证步骤

#### 步骤 1: 验证代理服务器
```bash
# 测试代理是否工作
curl -x http://127.0.0.1:7890 https://httpbin.org/ip
```

#### 步骤 2: 测试 Notion API
```bash
# 使用代理测试 Notion API
curl -x http://127.0.0.1:7890 \
     -H "Authorization: Bearer YOUR_NOTION_TOKEN_HERE" \
     -H "Notion-Version: 2022-06-28" \
     https://api.notion.com/v1/users/me
```

#### 步骤 3: 验证 Python 连接
```python
# 创建测试脚本
import requests

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}

try:
    response = requests.get(
        'https://api.notion.com/v1/users/me',
        headers={
            'Authorization': 'Bearer YOUR_NOTION_TOKEN_HERE',
            'Notion-Version': '2022-06-28'
        },
        proxies=proxies,
        verify=False
    )
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
except Exception as e:
    print(f'Error: {e}')
```

## ⚠️ 故障排除

### 问题 1: 400 Bad Request
**原因**: 代理配置错误或代理不支持 HTTPS
**解决方案**:
1. 禁用代理: `NOTION_PROXY = ""`
2. 或者使用正确的代理格式

### 问题 2: 连接超时
**原因**: 代理服务器响应慢或不稳定
**解决方案**:
1. 检查代理服务器状态
2. 尝试不同的代理端口
3. 考虑临时禁用代理

### 问题 3: SSL 证书错误
**原因**: 代理的 SSL 配置问题
**解决方案**:
1. 在代码中添加: `verify=False`
2. 或者配置正确的 SSL 证书

### 问题 4: 认证失败
**原因**: 代理需要认证但未配置
**解决方案**:
1. 目前系统不支持代理认证
2. 使用不需要认证的代理
3. 或完全禁用代理

## 🔍 调试命令

### 查看当前配置
```bash
python -c "
import config
print(f'Notion Token: {config.NOTION_TOKEN[:20]}...')
print(f'Notion Proxy: {config.NOTION_PROXY}')
print(f'Machines DB: {config.NOTION_DATABASES.get(\"machines\", \"Not set\")}')
"
```

### 测试数据库连接
```bash
python find_database_id.py 248a62a2-edb3-80d8-9c58-f242e2ee1db5
```

### 运行详细测试
```bash
python detailed_test.py
```

## 💡 推荐配置

### 最佳配置（推荐）
```python
# config.py
NOTION_PROXY = ""  # 禁用代理，直接连接
```

### 代理配置（如果需要）
```python
# config.py
NOTION_PROXY = "http://127.0.0.1:7890"  # 您的代理服务器
```

### 备用配置
如果主要代理不工作，可以尝试：
```python
NOTION_PROXY = "http://127.0.0.1:1080"  # 备选端口
```

## 📞 获取帮助

如果以上方法都无法解决问题：

1. **检查错误信息**: 运行 `python test_command.py` 查看具体错误
2. **验证代理**: 确认代理服务器正常工作
3. **检查网络**: 确保可以访问 `api.notion.com`
4. **联系支持**: 提供具体的错误信息和代理配置

## 🚀 快速修复

如果您急于使用功能，最快的解决方案是：

1. **编辑 config.py**:
   ```python
   NOTION_PROXY = ""  # 禁用代理
   ```

2. **重启应用**:
   ```bash
   # 停止当前运行的应用 (Ctrl+C)
   python app.py
   ```

3. **测试功能**:
   ```
   # 在QQ群中发送
   #machine_regions
   #machine_search 铁锭
   ```

这样应该可以立即解决问题！