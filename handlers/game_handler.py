# handlers/game_handler.py
import random
from utils.file_utils import load_json, dump_json
from utils.api_utils import send_group_message
import config

def handle_help_command(event):
    """处理 #help 命令"""
    group_id = event['group_id']

    help_text = (
        "🤖 QQ Bot 功能帮助\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🔐 AQL 功能 (仅对 haochang 群有效)\n"
        "  • .aql / #aql <账号名> - 查询账号动态码\n"
        "  • .aqladd / #aqladd <账号名> <密钥> - 添加AQL账号\n\n"

        "🎮 游戏管理功能\n"
        "  • #玩什么 - 随机选择游戏\n"
        "  • #游戏列表 - 查看所有游戏\n"
        "  • #添加游戏 <游戏名> - 添加游戏到列表\n"
        "  • #删除游戏 <游戏名> - 从列表删除游戏\n\n"

        "📺 万达游戏管理\n"
        "  • #wdhow - 随机选择万达游戏\n"
        "  • #wdlst - 查看所有万达游戏\n"
        "  • #wdadd <游戏名> - 添加万达游戏\n"
        "  • #wddel <游戏名> - 删除万达游戏\n\n"

        "🏠 Minecraft 游戏管理\n"
        "  • #mchow - 随机选择MC游戏\n"
        "  • #mclst - 查看所有MC游戏\n"
        "  • #mcadd <游戏名> - 添加MC游戏\n"
        "  • #mcdel <游戏名> - 删除MC游戏\n\n"

        "📝 Notion 日记功能\n"
        "  • #daily - 查看今日日记内容\n"
        "  • #add_daily - 创建今日日记页面\n"
        "  • #update_cover - 更新今日日记封面为Bing壁纸\n\n"

        "👤 @ 功能\n"
        "  • #at - 查询@信息\n"
        "  • #atadd <用户名> - 添加@信息\n"
        "  • #atls - 列出所有@信息\n"
        "  • #atdel <用户名> - 删除@信息\n\n"

        "❓ 帮助\n"
        "  • #help - 显示此帮助信息"
    )

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