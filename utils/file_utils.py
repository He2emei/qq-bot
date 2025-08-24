# utils/file_utils.py
import json

def load_json(path):
    """从指定路径加载JSON文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 如果文件不存在或为空，返回一个合理的默认值
        return {} if 'account' in path else []

def dump_json(path, content):
    """将内容写入指定路径的JSON文件"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)