#!/usr/bin/env python3
# test_command.py - 测试命令处理

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_command_matching():
    """测试命令匹配"""
    from app import COMMAND_ROUTER

    test_commands = [
        "#machine_search 铁锭",
        "#machine_region 江都市",
        "#machine_regions",
        "#mechine_search 铁锭",  # 拼写错误
        "#aql test",
        "#help"
    ]

    print("Testing command matching...")
    for cmd in test_commands:
        matched = False
        for route_cmd in COMMAND_ROUTER:
            if cmd.startswith(route_cmd):
                print(f"[MATCH] '{cmd}' -> '{route_cmd}' -> {COMMAND_ROUTER[route_cmd].__name__}")
                matched = True
                break
        if not matched:
            print(f"[NO MATCH] '{cmd}'")

def test_machine_handler():
    """测试机器处理器"""
    print("\nTesting machine handler...")

    # 模拟事件数据
    test_event = {
        'group_id': 123456,
        'user_id': 789012,
        'message': "#machine_search 铁锭"
    }

    try:
        from handlers.notion_handler import handle_notion_command
        print("Calling handle_notion_command...")
        handle_notion_command(test_event)
        print("Handler executed successfully")
    except Exception as e:
        print(f"Handler error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_command_matching()
    test_machine_handler()