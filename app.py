# app.py
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

import config

# 导入所有处理器
from handlers import aql_handler, game_handler, notion_handler, at_handler#, ai_handler, general_handler

# 启动 Notion 定时任务调度器 (需要安装 APScheduler 包)
# try:
#     from services.notion_scheduler import start_notion_scheduler
#     start_notion_scheduler()
# except Exception as e:
#     print(f"启动 Notion 调度器失败: {e}")

app = Flask(__name__)

# 命令路由器：将命令前缀映射到处理函数
# key: 命令前缀, value: 对应的处理函数
# 群组权限配置
GROUP_PERMISSIONS = {
    # 主群组：具有所有功能的权限
    'main_groups': [config.GROUP_IDS['default'], config.GROUP_IDS['me'], config.GROUP_IDS['game']],
    # AQL专用群组：只有AQL功能的权限
    'aql_groups': [config.GROUP_IDS['haochang']],
}

COMMAND_ROUTER = {
    '.aqladd': aql_handler.handle_aql_add,
    '#aqladd': aql_handler.handle_aql_add,
    '.aql': aql_handler.handle_aql,
    '#aql': aql_handler.handle_aql,

    # 游戏相关命令
    '#游戏列表': game_handler.handle_game_command,
    '#添加游戏': game_handler.handle_game_command,
    '#删除游戏': game_handler.handle_game_command,
    '#玩什么': game_handler.handle_game_command,
    '#wdlst': game_handler.handle_game_command,
    '#wdadd': game_handler.handle_game_command,
    '#wddel': game_handler.handle_game_command,
    '#wdhow': game_handler.handle_game_command,
    '#mclst': game_handler.handle_game_command,
    '#mcadd': game_handler.handle_game_command,
    '#mcdel': game_handler.handle_game_command,
    '#mchow': game_handler.handle_game_command,

    # Notion 相关命令
    '#daily': notion_handler.handle_notion_command,
    '#add_daily': notion_handler.handle_notion_command,
    '#update_cover': notion_handler.handle_notion_command,

    # @ 相关命令
    '#at': at_handler.handle_at_command,
    '#atadd': at_handler.handle_at_add,
    '#atls': at_handler.handle_at_list,
    '#atdel': at_handler.handle_at_delete,

    # 帮助命令
    '#help': game_handler.handle_help_command,

    # ... 您可以继续添加其他命令的映射
    # '#dsr1': ai_handler.handle_dsr1,
    # '.yqm': general_handler.handle_yqm,
}

# 命令权限分类
AQL_COMMANDS = {'.aqladd', '#aqladd', '.aql', '#aql'}
MAIN_COMMANDS = {cmd for cmd in COMMAND_ROUTER.keys() if cmd not in AQL_COMMANDS}

def _check_command_permission(group_id: int, command: str) -> bool:
    """检查命令是否被允许在指定群组中执行"""
    # AQL命令只能在AQL专用群组中执行
    if command in AQL_COMMANDS:
        return group_id in GROUP_PERMISSIONS['aql_groups']
    # 主功能命令可以在主群组中执行
    elif command in MAIN_COMMANDS:
        return group_id in GROUP_PERMISSIONS['main_groups']
    # 默认允许（虽然不应该发生）
    return False


def get_message_text(message_objects):
    """从消息对象中提取纯文本内容"""
    return ''.join([m['data']['text'] for m in message_objects if m['type'] == 'text']).strip()


def get_full_message_content(event_data):
    """从事件数据中提取完整消息内容，包括文本和图片"""
    message_objects = event_data.get('message', [])

    content_parts = []

    for msg_obj in message_objects:
        if msg_obj['type'] == 'text':
            # 添加文本内容
            text = msg_obj['data']['text'].strip()
            if text:
                content_parts.append(text)
        elif msg_obj['type'] == 'image':
            # 添加图片URL
            image_url = msg_obj['data'].get('url', '')
            if image_url:
                content_parts.append(f"[CQ:image,url={image_url}]")

    return ''.join(content_parts).strip()


@app.route('/', methods=['POST'])
def receive_event():
    event_data = request.json
    print(event_data)

    # 基本的事件校验
    if not event_data or event_data.get('post_type') != 'message' or event_data.get('message_type') != 'group':
        return "Not a group message event", 200

    group_id = event_data.get('group_id')
    if group_id not in config.MONITORED_GROUPS:
        return "Group not monitored", 200

    message_text = get_message_text(event_data.get('message', []))
    if not message_text:
        return "Empty message", 200

    print(f"Received from group {group_id}: {message_text}")

    # 将消息文本注入回event_data，方便处理器使用
    event_data['message'] = message_text

    matched_command = None
    # 查找匹配的命令
    for command in COMMAND_ROUTER:
        if message_text.startswith(command):
            matched_command = command
            print(f"Command matched: '{command}' for message: '{message_text}'")
            break

    if not matched_command:
        return "OK", 200  # 没有匹配的命令，正常响应

    # 检查群组权限
    if not _check_command_permission(group_id, matched_command):
        print(f"Permission denied for command '{matched_command}' in group {group_id}")
        return "Command not permitted for this group", 200

    # 根据命令前缀分发到对应的处理器
    for command, handler_func in COMMAND_ROUTER.items():
        if message_text.startswith(command):
            # 找到匹配的命令，调用处理器并停止查找
            try:
                handler_func(event_data)
            except Exception as e:
                print(f"Error handling command '{command}': {e}")
            break # 每个消息只处理一次

    return "OK", 200


if __name__ == '__main__':
    app.run(host=config.SERVER_HOST, port=config.SERVER_PORT)
