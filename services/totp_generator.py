# services/totp_generator.py
import pyotp
import time
import sys
import os

# 将项目根目录添加到Python路径，以便导入config和utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_utils import load_json, dump_json
import config

def generate_codes():
    """生成并保存TOTP验证码"""
    auth_file = load_json(config.DATA_PATHS['auth_list'])
    code_file = load_json(config.DATA_PATHS['code']) or {}

    auth_list = auth_file.get("list", [])
    if not auth_list:
        print("认证列表为空，不生成code。")
        return

    for item in auth_list:
        try:
            totp = pyotp.TOTP(item["secret"], digits=8, interval=30, digest='sha1')
            code_file[item["account"]] = totp.now()
        except Exception as e:
            print(f"为账户 {item.get('account')} 生成code时出错: {e}")

    dump_json(config.DATA_PATHS['code'], code_file)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Code文件已更新。")

if __name__ == '__main__':
    print("TOTP生成服务已启动...")
    while True:
        current_second = time.localtime().tm_sec
        # 在每分钟的0秒和30秒时执行
        if current_second in [0, 30]:
            generate_codes()
            time.sleep(1) # 防止在一秒内重复执行
        
        time.sleep(0.5) # 降低CPU占用