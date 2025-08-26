# test_faq.py
#!/usr/bin/env python3
"""测试FAQ功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_manager import database_manager
from handlers.faq_handler import handle_faq_query, handle_faq_edit, handle_faq_command

def test_database_operations():
    """测试数据库操作"""
    print("=== 测试数据库操作 ===")

    # 测试设置FAQ内容
    key = "test_key"
    content = "这是测试内容，支持图片：https://example.com/image.jpg"
    success = database_manager.set_faq_content(key, content)
    print(f"设置FAQ内容: {'成功' if success else '失败'}")

    # 测试获取FAQ内容
    retrieved_content = database_manager.get_faq_content(key)
    print(f"获取FAQ内容: {retrieved_content}")

    # 测试获取不存在的key
    nonexistent_content = database_manager.get_faq_content("nonexistent_key")
    print(f"获取不存在的key: {nonexistent_content}")

    # 测试覆盖内容
    new_content = "这是更新后的内容"
    success = database_manager.set_faq_content(key, new_content)
    print(f"覆盖FAQ内容: {'成功' if success else '失败'}")

    retrieved_content = database_manager.get_faq_content(key)
    print(f"获取更新后的内容: {retrieved_content}")

    print()

def test_handler_functions():
    """测试处理器函数"""
    print("=== 测试处理器函数 ===")

    # 模拟事件数据
    def create_mock_event(message_text, group_id=123456):
        return {
            'message': message_text,
            'group_id': group_id
        }

    # 测试查询不存在的key
    print("测试查询不存在的key:")
    event = create_mock_event('#faq nonexistent_key')
    handle_faq_query(event)

    # 测试编辑FAQ
    print("\n测试编辑FAQ:")
    event = create_mock_event('#faq edit test_key_from_handler 这是通过处理器设置的内容')
    handle_faq_edit(event)

    # 测试查询存在的key
    print("\n测试查询存在的key:")
    event = create_mock_event('#faq test_key_from_handler')
    handle_faq_query(event)

    # 测试主入口函数
    print("\n测试主入口函数:")
    event = create_mock_event('#faq unknown_command')
    handle_faq_command(event)

    print()

if __name__ == "__main__":
    print("开始测试FAQ功能...\n")

    # 测试数据库操作
    test_database_operations()

    # 测试处理器函数
    test_handler_functions()

    print("测试完成！")