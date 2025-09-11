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
    while at_txt:
        e = at_txt[0]
        if e in qq_dic:
            if qq_dic[e] not in qq_ls:
                qq_ls.append(qq_dic[e])
        elif e in nick_dic:
            at_txt.extend(nick_dic[e])
        del at_txt[0]

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
    at_data = load_json(config.DATA_PATHS['at'])
    send_group_message(group_id, f"当前昵称配置：{at_data['nickname']}")

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
        for qq in nk_txt[1:]:
            try:
                at_data["nickname"][nickname].remove(qq)
                msg = f"已从昵称 {nickname} 中除去 {nk_txt[1:]}"
            except ValueError:
                msg = f"昵称 {nickname} 中未找到 {qq}"
    else:
        # 删除整个昵称
        try:
            del at_data["nickname"][nickname]
            msg = f"已删除昵称 {nickname}"
        except KeyError:
            msg = f"未找到昵称 {nickname}"

    dump_json(config.DATA_PATHS['at'], at_data)
    send_group_message(group_id, msg)