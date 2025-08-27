# test_faq.py
#!/usr/bin/env python3
"""测试FAQ功能"""

import sys
import os
# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_manager import database_manager
from handlers.faq_handler import handle_faq_query, handle_faq_edit, handle_faq_command, handle_faq_list, handle_faq_delete

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

def test_content_conversion():
    """测试内容转换功能"""
    print("=== 测试内容转换功能 ===")

    from handlers.faq_handler import convert_content_to_cq

    # 测试纯文本
    text_content = "这是一段纯文本内容"
    converted = convert_content_to_cq(text_content)
    print(f"纯文本转换: {converted}")

    # 测试带图片URL的文本
    image_content = "这是带图片的内容: https://example.com/image.jpg 和 https://test.com/pic.png"
    converted = convert_content_to_cq(image_content)
    print(f"图片URL转换: {converted}")

    # 测试已经是CQ码的内容
    cq_content = "这是已经包含CQ码的内容: [CQ:image,url=https://example.com/image.jpg]"
    converted = convert_content_to_cq(cq_content)
    print(f"CQ码内容转换: {converted}")

    # 测试混合内容
    mixed_content = "规则说明:\n1. 第一条规则\n2. 第二条规则 https://example.com/rule.jpg\n3. 第三条规则"
    converted = convert_content_to_cq(mixed_content)
    print(f"混合内容转换: {converted}")

    print()

def test_new_faq_features():
    """测试新增的FAQ功能：列表查询和删除"""
    print("=== 测试新增的FAQ功能 ===")

    # 模拟事件数据
    def create_mock_event(message_text, group_id=123456):
        return {
            'message': message_text,
            'group_id': group_id
        }

    # 首先创建一些测试数据
    print("创建测试数据...")
    database_manager.set_faq_content("test_list_1", "这是第一个测试FAQ")
    database_manager.set_faq_content("test_list_2", "这是第二个测试FAQ")
    database_manager.set_faq_content("test_delete_me", "这个FAQ将被删除")

    # 测试列出FAQ列表
    print("\n测试列出FAQ列表:")
    event = create_mock_event('#faq list')
    handle_faq_list(event)

    # 测试删除存在的FAQ
    print("\n测试删除存在的FAQ:")
    event = create_mock_event('#faq delete test_delete_me')
    handle_faq_delete(event)

    # 测试删除不存在的FAQ
    print("\n测试删除不存在的FAQ:")
    event = create_mock_event('#faq delete nonexistent_key')
    handle_faq_delete(event)

    # 再次列出FAQ列表，确认删除成功
    print("\n删除后再次列出FAQ列表:")
    event = create_mock_event('#faq list')
    handle_faq_list(event)

    # 测试主入口函数的新命令
    print("\n测试主入口函数的新命令:")

    # 测试#faq help命令
    print("\n测试#faq help命令:")
    event = create_mock_event('#faq help')
    handle_faq_command(event)

    # 测试#faq list命令
    event = create_mock_event('#faq list')
    handle_faq_command(event)

    # 测试#faq delete命令
    event = create_mock_event('#faq delete test_list_1')
    handle_faq_command(event)

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

    # 测试编辑FAQ（包含图片URL）
    print("\n测试编辑FAQ（包含图片URL）:")
    event = create_mock_event('#faq edit test_key_with_image 这是一个包含图片的FAQ: https://example.com/faq-image.jpg')
    handle_faq_edit(event)

    # 测试编辑FAQ（模拟真实图片消息）
    print("\n测试编辑FAQ（模拟真实图片消息）:")
    mock_event_with_image = {
        'message': '#faq edit test_key_real_image 这是包含真实图片的消息:[CQ:image,url=https://multimedia.nt.qq.com.cn/download?appid=1407&fileid=test]',
        'group_id': 123456
    }
    handle_faq_edit(mock_event_with_image)

    # 测试查询存在的key
    print("\n测试查询存在的key:")
    event = create_mock_event('#faq test_key_from_handler')
    handle_faq_query(event)

    # 测试查询带图片的key
    print("\n测试查询带图片的key:")
    event = create_mock_event('#faq test_key_with_image')
    handle_faq_query(event)

    # 测试查询真实图片的key
    print("\n测试查询真实图片的key:")
    event = create_mock_event('#faq test_key_real_image')
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

    # 测试内容转换功能
    test_content_conversion()

    # 测试新增的FAQ功能
    test_new_faq_features()

    # 测试处理器函数
    test_handler_functions()

    print("测试完成！")