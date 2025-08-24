# handlers/game_handler.py
import random
from utils.file_utils import load_json, dump_json
from utils.api_utils import send_group_message
import config

def handle_help_command(event):
    """处理 #help 命令"""
    group_id = event['group_id']
    from utils.file_utils import load_json
    import config

    help_data = load_json(config.DATA_PATHS['help'])
    help_text = help_data.get('text', '帮助信息未配置')
    send_group_message(group_id, help_text)

def handle_game_command(event):
    """处理所有与游戏、WD、MC相关的命令"""
    group_id = event['group_id']
    message = event['message'].strip()

    command_map = {
        '#游戏列表': ('game_list', 'list'),
        '#添加游戏': ('game_list', 'add'),
        '#删除游戏': ('game_list', 'del'),
        '#玩什么': ('game_list', 'random'),
        '#wdlst': ('wd_list', 'list'),
        '#wdadd': ('wd_list', 'add'),
        '#wddel': ('wd_list', 'del'),
        '#wdhow': ('wd_list', 'random'),
        '#mclst': ('mc_list', 'list'),
        '#mcadd': ('mc_list', 'add'),
        '#mcdel': ('mc_list', 'del'),
        '#mchow': ('mc_list', 'random'),
    }

    for cmd_prefix, (key, action) in command_map.items():
        if message.startswith(cmd_prefix):
            path = config.DATA_PATHS[key]
            game_lst = load_json(path)
            
            if action == 'list':
                msg = '\n'.join(str(e) for e in game_lst)
                send_group_message(group_id, msg)
                return

            if action == 'random':
                if game_lst:
                    random_gm = random.choice(game_lst)
                    send_group_message(group_id, random_gm)
                else:
                    send_group_message(group_id, "列表是空的，我也不知道玩什么。")
                return

            # Add and Del actions
            content = message[len(cmd_prefix):].strip()
            if not content:
                send_group_message(group_id, "请输入要操作的内容。")
                return
            
            if action == 'add':
                if content not in game_lst:
                    game_lst.append(content)
                    dump_json(path, game_lst)
                    send_group_message(group_id, "添加成功")
                else:
                    send_group_message(group_id, "这个已经在列表里啦。")
                return

            if action == 'del':
                if content in game_lst:
                    game_lst.remove(content)
                    dump_json(path, game_lst)
                    send_group_message(group_id, "删除成功")
                else:
                    send_group_message(group_id, "列表里没有这个哦。")
                return