# scripts/process_yqm.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_utils import dump_json
import config

# 从原始 yqm.py 中复制的数据
raw_data = '''fdf7cf3a3583f3de48be49b4ef7aa3f3	2024-12-14 22:01:26
... (此处省略了您提供的所有数据) ...
f16fe3cfdf1947937d3e4eb8437a1ad4	2024-12-14 22:01:26'''

def extract_and_save_yqm(data):
    """提取邀请码并保存到JSON文件"""
    lines = data.strip().split("\n")
    yqm_codes = [line.split()[0] for line in lines if line]
    
    output_path = config.DATA_PATHS['yqm']
    dump_json(output_path, yqm_codes)
    print(f"成功提取 {len(yqm_codes)} 个邀请码并保存到 {output_path}")

if __name__ == '__main__':
    extract_and_save_yqm(raw_data)