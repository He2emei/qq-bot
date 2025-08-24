import base64
from utils.file_utils import load_json, dump_json
from utils.api_utils import send_group_message, get_dynamic_code_2
import config

def hex_to_bytes(hex_str):
    return bytes.fromhex(hex_str)

def convert_to_base32(hex_str):
    byte_data = hex_to_bytes(hex_str)
    return base64.b32encode(byte_data).decode('utf-8')

def handle_aql(event):
    """处理 .aql 和 #aql 命令"""
    group_id = event['group_id']
    user_id = event['user_id']
    message = event['message']
    
    key = message[5:].strip()

    if group_id in [config.GROUP_IDS['jjl_test'], config.GROUP_IDS['jjl']]:
        # 新逻辑 for jjl群
        accounts = load_json(config.DATA_PATHS['ze_account'])
        if key in accounts:
            token = accounts[key]
            code = get_dynamic_code_2(token)
            response_msg = f"[CQ:at,qq={user_id}] {code}" if code else f"[CQ:at,qq={user_id}] 获取动态码失败"
        else:
            response_msg = f"[CQ:at,qq={user_id}] 账户错误或不存在"
    else:
        # 原逻辑 for 其他群
        accounts = load_json(config.DATA_PATHS['code'])
        if key in accounts:
            value = accounts[key]
            response_msg = f"[CQ:at,qq={user_id}] {value}"
        else:
            response_msg = f"[CQ:at,qq={user_id}] 账户错误或不存在"
            
    send_group_message(group_id, response_msg)


def handle_aql_add(event):
    """处理 .aqladd 和 #aqladd 命令"""
    group_id = event['group_id']
    message = event['message']
    
    parts = message[8:].split()
    if len(parts) < 2:
        send_group_message(group_id, "格式错误，请使用 .aqladd <账户> <密钥>")
        return

    account, secret = parts[0], parts[1]

    if group_id == config.GROUP_IDS['jjl_test']:
        # jjl_test群的逻辑
        na_path = config.DATA_PATHS['ze_account']
        na_json = load_json(na_path)
        na_json[account] = secret
        dump_json(na_path, na_json)
        send_group_message(group_id, f"已将 {account} 安全令信息添加")
    
    elif group_id == config.GROUP_IDS['gl']:
        # gl群的逻辑
        if len(secret) == 40:
            secret = convert_to_base32(secret)
        
        na_path = config.DATA_PATHS['auth_list']
        na_json = load_json(na_path)
        
        if not na_json.get('list'): # 初始化
             na_json['list'] = []

        new_id = na_json['list'][-1]['id'] + 1 if na_json['list'] else 1
        
        new_item = {
            'id': new_id,
            'name': 'None',
            'account': account,
            'secret': secret
        }
        na_json['list'].append(new_item)
        dump_json(na_path, na_json)
        send_group_message(group_id, f"已将 {account} 安全令信息添加")