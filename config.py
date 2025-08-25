# config.py
import os

# NapCat QQ机器人框架配置
NAPCAT_BASE_URL = "http://127.0.0.1:23333"

# 外部服务URL
JJL_BASE_URL = 'http://yunma.xyq5.top/'
JJL_QUERY_URL = JJL_BASE_URL + 'api/api_query'
DYNAMIC_CODE_URL = 'http://47.115.143.149:99/'

# OpenAI / 腾讯知识引擎 API 配置
OPENAI_API_KEY = "sk-XdT9a5PXGPCWGyGiZ78jUpbkrVROi5ef2SqJV2iyItRUlvMa" # 注意：请妥善保管您的API Key
OPENAI_BASE_URL = "https://api.lkeap.cloud.tencent.com/v1"

# QQ群号配置
GROUP_IDS = {
    'default': 1011696295,
    'yqm': 176518586,
    'game': 491372741,
    'gl': 767712912,
    'me': 1022453604,
    'jjl_test': 948937168,
    'jjl': 1042637919,
    'another_group': 107013467,
    'mc_group': 612488213
}

# 监控所有已配置的群聊
MONITORED_GROUPS = set(GROUP_IDS.values())

# 数据文件路径配置 (相对于项目根目录)
DATA_PATHS = {
    'code': 'data/code.json',
    'ze_account': 'data/ze_account.json',
    'yqm': 'data/yqm.json',
    'game_list': 'data/gameList.json',
    'wd_list': 'data/wd.json',
    'mc_list': 'data/mc.json',
    'help': 'data/help.json',
    'at': 'data/at.json',
    'auth_list': 'data/authenticatorList.json',
    'memory': 'data/memory.json'
}

# Flask 服务配置
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 7778

# === Notion 配置 ===
# Notion API 配置
# 注意：请将以下token替换为您的实际token，或使用环境变量
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "your_notion_token_here")  # 用于机器、地域和产物查询
NOTION_TOKEN_DIARY = os.getenv("NOTION_TOKEN_DIARY", "your_notion_diary_token_here")  # 用于日记相关操作
NOTION_VERSION = "2022-06-28"

# Notion 数据库配置
NOTION_DATABASES = {
    'daily': '32ace5e970b647e784d4d96ced0b2528',      # Daily Dairy 2.0
    'weekly': 'b933933868254b769bf96e3768b1dbda',    # Weekly Dairy 2.0
    'terms': 'ec2a978cd73e43d49ddf41693e68fc15',     # Terms Dairy 2.0
    'machines': '248a62a2-edb3-80d8-9c58-f242e2ee1db5',   # 核心服机器数据库
    'products': '248a62a2-edb3-8027-9549-fc0663a5aa3b',   # 产物数据库
    'regions': '248a62a2-edb3-8079-9226-c2b3c3f1e63e',    # 地域数据库
    'database1': '248a62a2-edb3-8027-9549-fc0663a5aa3b',  # 第二个数据库 (产物)
    'database2': '248a62a2-edb3-8079-9226-c2b3c3f1e63e'   # 第三个数据库 (地域)
}

# Notion 代理配置 (如果需要)
NOTION_PROXY = ""  # 设置为空字符串禁用代理，设置为"http://proxy:port"启用代理

# Notion 数据文件路径
NOTION_DATA_PATHS = {
    'daily_template': 'data/notion_templates/daily_template.json',
    'weekly_template': 'data/notion_templates/weekly_template.json',
    'cache': 'data/notion_cache.json'
}
