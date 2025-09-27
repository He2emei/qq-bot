# AI 开发指南

## 项目架构概述

这是一个基于Flask的QQ机器人后端系统，使用NapCat框架与QQ客户端进行HTTP通信。主要用于处理QQ群聊消息，提供多种功能服务。

### 核心架构

**主应用层 (app.py)**
- Flask服务器，监听POST请求接收QQ消息
- 消息命令路由器，根据消息前缀分发到不同处理器
- 基础事件校验，只处理指定群组的群聊消息

**处理器层 (handlers/)**
- `aql_handler.py`: 处理AQL查询相关命令
- `at_handler.py`: 处理@提醒功能
- `faq_handler.py`: 处理FAQ查询、编辑、删除等操作
- `game_handler.py`: 处理游戏列表管理、随机选择等
- `notion_handler.py`: 处理Notion日记相关功能

**服务层 (services/)**
- `database_manager.py`: SQLite数据库管理FAQ数据
- `notion_service.py`: Notion API服务，包含日记管理器
- `notion_scheduler.py`: 定时任务调度器，自动创建日记页面
- `totp_generator.py`: TOTP验证码生成服务

**工具层 (utils/)**
- `api_utils.py`: 群消息发送、验证码获取、AI响应调用
- `file_utils.py`: JSON文件读写操作
- `image_utils.py`: FAQ图片下载和管理
- `notion_utils.py`: Notion块处理、过滤器创建等

**配置管理**
- `config.py`: 主要配置文件（API密钥、群号、路径等）
- `config_manager.py`: 敏感配置文件管理，避免git冲突
- `init_configs.py`: 配置初始化脚本

**数据存储 (data/)**
- JSON配置文件：游戏列表、@提醒、认证器等
- SQLite数据库：FAQ数据存储
- Notion模板文件：日记模板配置

## 更新说明

每次项目更新时，需要在`docs/`目录下创建一个新的Markdown文档，用于记录本次更新的内容和影响。命名时在最后要加上如"_202509280116"这样的时间标识。

## 开发注意事项

- 当某个功能存在问题时，应当在解决问题的同时分析问题的核心，并考虑代码中有没有类似地方存在同样问题。尤其是同个功能下多个具有较小差别的关键词在处理时遇到的问题往往相同。
- 当完成任务后，请自动添加并推送到git远程仓库。同时，commit信息请用中文撰写。

## 测试指导

### 环境说明
与程序进行HTTP连接的QQ客户端在代码编辑的机器上（本地电脑）并不会运行。因此在本地测试时，可以忽略QQ客户端连接相关问题，自行创建消息测试样本来验证功能。

### 测试消息样本

#### 1. 普通文字消息
```python
{
    'self_id': 1919447403,
    'user_id': 1659388154,
    'time': 1758991842,
    'message_id': 1358101407,
    'message_seq': 1358101407,
    'real_id': 1358101407,
    'real_seq': '676',
    'message_type': 'group',
    'sender': {
        'user_id': 1659388154,
        'nickname': '提拉米苏',
        'card': '',
        'role': 'owner'
    },
    'raw_message': '普通文本',
    'font': 14,
    'sub_type': 'normal',
    'message': [{'type': 'text', 'data': {'text': '普通文本'}}],
    'message_format': 'array',
    'post_type': 'message',
    'group_id': 638227713
}
```

#### 2. 戳一戳消息
```python
{
    'time': 1758992021,
    'self_id': 1919447403,
    'post_type': 'notice',
    'notice_type': 'notify',
    'sub_type': 'poke',
    'target_id': 1919447403,
    'user_id': 1659388154,
    'group_id': 638227713,
    'raw_info': [
        {'col': '1', 'nm': '', 'type': 'qq', 'uid': 'u_LfP_k7bCvpXm0egYQZUrCw'},
        {'jp': 'https://zb.vip.qq.com/v2/pages/nudgeMall?_wv=2&actionId=0', 'src': 'http://tianquan.gtimg.cn/nudgeaction/item/0/expression.jpg', 'type': 'img'},
        {'txt': '戳了戳', 'type': 'nor'},
        {'col': '1', 'nm': '', 'tp': '0', 'type': 'qq', 'uid': 'u_RR66sUvEd1iud92VER_gPQ'},
        {'txt': '', 'type': 'nor'}
    ]
}
```

#### 3. 图片消息
```python
{
    'self_id': 1919447403,
    'user_id': 1659388154,
    'time': 1758992057,
    'message_id': 1262836845,
    'message_seq': 1262836845,
    'real_id': 1262836845,
    'real_seq': '677',
    'message_type': 'group',
    'sender': {
        'user_id': 1659388154,
        'nickname': '提拉米苏',
        'card': '',
        'role': 'owner'
    },
    'raw_message': '[CQ:image,file=41A1002D131E1D7BDB10A0BA671A1808.png,sub_type=0,url=https://multimedia.nt.qq.com.cn/download?appid=1407&fileid=EhR_RG7F8iQn46_DJvpL0VYEi5O6MRivTCD_Ciij76mFtPmPAzIEcHJvZFCAvaMBWhA3oYuM1WEez_5QYbwrJsa4egKBWIIBAm5q&rkey=CAESMCcdrR7JCBEmBuxAdazhT9lVccBlKo3i4ditWvW851Y9oUDaIaEWcIw8hORh_GGs6g,file_size=9775]',
    'font': 14,
    'sub_type': 'normal',
    'message': [{
        'type': 'image',
        'data': {
            'summary': '',
            'file': '41A1002D131E1D7BDB10A0BA671A1808.png',
            'sub_type': 0,
            'url': 'https://multimedia.nt.qq.com.cn/download?appid=1407&fileid=EhR_RG7F8iQn46_DJvpL0VYEi5O6MRivTCD_Ciil76mFtPmPAzIEcHJvZFCAvaMBWhA3oYuM1WEez_5QYbwrJsa4egKBWIIBAm5q&rkey=CAESMCcdrR7JCBEmBuxAdazhT9lVccBlKo3i4ditWvW851Y9oUDaIaEWcIw8hORh_GGs6g',
            'file_size': '9775'
        }
    }],
    'message_format': 'array',
    'post_type': 'message',
    'group_id': 638227713
}
```

#### 4. 图片混合消息
```python
{
    'self_id': 1919447403,
    'user_id': 1659388154,
    'time': 1758992087,
    'message_id': 1425899392,
    'message_seq': 1425899392,
    'real_id': 1425899392,
    'real_seq': '678',
    'message_type': 'group',
    'sender': {
        'user_id': 1659388154,
        'nickname': '提拉米苏',
        'card': '',
        'role': 'owner'
    },
    'raw_message': '123[CQ:image,file=41A1002D131E1D7BDB10A0BA671A1808.png,sub_type=0,url=https://multimedia.nt.qq.com.cn/download?appid=1407&fileid=EhR_RG7F8iQn46_DJvpL0VYEi5O6MRivTCD_CiilguuTtPmPAzIEcHJvZFCAvaMBWhAM9zQ9MVBsul2tIB9Myki-egJlNYIBAm5q&rkey=CAESMCcdrR7JCBEmBuxAdazhT9lVccBlKo3i4ditWvW851Y9oUDaIaEWcIw8hORh_GGs6g,file_size=9775]',
    'font': 14,
    'sub_type': 'normal',
    'message': [
        {'type': 'text', 'data': {'text': '123'}},
        {
            'type': 'image',
            'data': {
                'summary': '',
                'file': '41A1002D131E1D7BDB10A0BA671A1808.png',
                'sub_type': 0,
                'url': 'https://multimedia.nt.qq.com.cn/download?appid=1407&fileid=EhR_RG7F8iQn46_DJvpL0VYEi5O6MRivTCD_CiilguuTtPmPAzIEcHJvZFCAvaMBWhAM9zQ9MVBsul2tIB9Myki-egJlNYIBAm5q&rkey=CAESMCcdrR7JCBEmBuxAdazhT9lVccBlKo3i4ditWvW851Y9oUDaIaEWcIw8hORh_GGs6g',
                'file_size': '9775'
            }
        }
    ],
    'message_format': 'array',
    'post_type': 'message',
    'group_id': 638227713
}
```

### 本地测试注意事项
- 本机为Windows系统，测试时请使用Windows兼容的代码
- AI（你）目前使用的终端是powershell，而使用者习惯cmd。所以你在运行命令时应符合powershell的规则，而指导我时请注明需要使用powershell或者默认使用cmd命令。
- 可通过创建上述格式的测试消息字典来模拟QQ消息输入
- 重点测试命令前缀匹配和处理器逻辑，无需实际连接QQ客户端