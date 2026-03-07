# handlers/at_handler.py
from utils.file_utils import load_json, dump_json
from utils.api_utils import send_group_message
import config

def handle_at_command(event):
    """处理 #at 命令"""
    group_id = event['group_id']
    user_id = event['user_id']
    message = event['message'].strip()

    if not message.startswith('#at ') or len(message) <= 4:
        return

    at_txt = message[4:].split()
    at_data = load_json(config.DATA_PATHS['at'])
    qq_dic = at_data['QQ']
    nick_dic = at_data['nickname']

    qq_ls = []
    visited_nicks = set()
    while at_txt:
        e = at_txt.pop(0)
        if e in qq_dic:
            if qq_dic[e] not in qq_ls:
                qq_ls.append(qq_dic[e])
        elif e in nick_dic:
            if e not in visited_nicks:
                visited_nicks.add(e)
                at_txt.extend(nick_dic[e])
        elif e.isdigit():
            qq_int = int(e)
            if qq_int not in qq_ls:
                qq_ls.append(qq_int)

    qq_msg = ''
    for e in qq_ls:
        if e != user_id:
            qq_msg += f"[CQ:at,qq={e}]"

    if qq_msg:
        send_group_message(group_id, qq_msg)
    else:
        send_group_message(group_id, "未找到有效的@对象")

def handle_at_add(event):
    """处理 #atadd 命令"""
    group_id = event['group_id']
    message = event['message'].strip()

    if not message.startswith('#atadd ') or len(message) <= 7:
        send_group_message(group_id, "格式错误，请使用 #atadd <昵称> <QQ号1> [QQ号2] ...")
        return

    nk_txt = message[7:].split()
    if len(nk_txt) < 2:
        send_group_message(group_id, "格式错误，请使用 #atadd <昵称> <QQ号1> [QQ号2] ...")
        return

    at_data = load_json(config.DATA_PATHS['at'])
    nickname = nk_txt[0]
    qq_numbers = nk_txt[1:]

    if nickname not in at_data["nickname"]:
        at_data["nickname"][nickname] = qq_numbers
    else:
        at_data["nickname"][nickname] = list(set(qq_numbers + at_data["nickname"][nickname]))

    dump_json(config.DATA_PATHS['at'], at_data)
    msg = f"已设定昵称 {nickname} 包含 {qq_numbers}"
    send_group_message(group_id, msg)

def handle_at_list(event):
    """处理 #atls 命令"""
    group_id = event['group_id']
    try:
        at_data = load_json(config.DATA_PATHS['at'])
        if 'nickname' in at_data and 'QQ' in at_data:
            msg = "【个人别名映射】\n"
            for nick, qq in at_data['QQ'].items():
                msg += f"{nick}: {qq}\n"
            
            msg += "\n【群组配置】\n"
            for group, members in at_data['nickname'].items():
                msg += f"{group}: {', '.join(members)}\n"
            
            send_group_message(group_id, msg.strip())
        else:
            send_group_message(group_id, "配置数据格式错误")
    except Exception as e:
        print(f"#atls 数据加载失败: {e}")
        send_group_message(group_id, "加载数据时出错，请稍后再试")

def handle_at_delete(event):
    """处理 #atdel 命令"""
    group_id = event['group_id']
    message = event['message'].strip()

    if not message.startswith('#atdel ') or len(message) <= 7:
        send_group_message(group_id, "格式错误，请使用 #atdel <昵称> [QQ号1] [QQ号2] ...")
        return

    nk_txt = message[7:].split()
    if len(nk_txt) < 1:
        send_group_message(group_id, "格式错误，请使用 #atdel <昵称> [QQ号1] [QQ号2] ...")
        return

    at_data = load_json(config.DATA_PATHS['at'])
    nickname = nk_txt[0]

    if len(nk_txt) > 1:
        # 删除指定QQ号
        success_removed = []
        failed_removed = []
        for qq in nk_txt[1:]:
            try:
                at_data["nickname"][nickname].remove(qq)
                success_removed.append(qq)
            except ValueError:
                failed_removed.append(qq)
        
        msg = f"已针对昵称 {nickname} 执行删除操作。"
        if success_removed:
            msg += f"\n成功移除: {', '.join(success_removed)}"
        if failed_removed:
            msg += f"\n未找到: {', '.join(failed_removed)}"
    else:
        # 删除整个昵称
        try:
            del at_data["nickname"][nickname]
            msg = f"已删除群组/昵称 {nickname}"
        except KeyError:
            msg = f"未找到群组/昵称 {nickname}"

    dump_json(config.DATA_PATHS['at'], at_data)
    send_group_message(group_id, msg)