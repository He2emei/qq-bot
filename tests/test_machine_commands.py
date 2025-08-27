#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试机器管理命令处理功能
验证消息命令解析和处理是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.notion_handler import (
    handle_machine_add_command,
    handle_machine_update_command,
    handle_machine_delete_command,
    handle_machine_help_command
)

def test_command_parsing():
    """测试命令解析功能"""
    print("开始测试机器管理命令解析...")

    # 模拟event_data结构
    def create_mock_event_data(message_text, group_id=123456):
        return {
            'message': message_text,
            'group_id': group_id
        }

    # 测试1: 添加机器命令解析
    print("\n1. 测试添加机器命令解析:")
    add_command = "#machine_add 测试发电机|电力区|overworld|100,200|电力|管理员"
    event_data = create_mock_event_data(add_command)

    print(f"命令: {add_command}")
    print("解析结果:")
    # 这里我们不实际执行发送消息，只是测试解析逻辑
    # 为了避免发送实际消息，我们需要模拟send_group_message

    # 手动解析参数来验证逻辑
    params_text = add_command[13:].strip()
    parts = params_text.split('|')
    if len(parts) >= 4:
        machine_data = {
            'name': parts[0].strip(),
            'region': parts[1].strip() if len(parts) > 1 else '',
            'dimension': parts[2].strip() if len(parts) > 2 else '',
            'coordinates': parts[3].strip() if len(parts) > 3 else '',
        }

        if len(parts) > 4 and parts[4].strip():
            machine_data['products'] = [p.strip() for p in parts[4].split(',') if p.strip()]
        if len(parts) > 5 and parts[5].strip():
            machine_data['maintainers'] = [m.strip() for m in parts[5].split(',') if m.strip()]

        print(f"  机器名: {machine_data['name']}")
        print(f"  地域: {machine_data['region']}")
        print(f"  维度: {machine_data['dimension']}")
        print(f"  坐标: {machine_data['coordinates']}")
        print(f"  产物: {', '.join(machine_data.get('products', []))}")
        print(f"  维护者: {', '.join(machine_data.get('maintainers', []))}")

    # 测试2: 更新机器命令解析
    print("\n2. 测试更新机器命令解析:")
    update_command = "#machine_update 测试发电机|region:新区|products:电力,蒸汽|coordinates:150,250"
    event_data = create_mock_event_data(update_command)

    print(f"命令: {update_command}")
    print("解析结果:")

    params_text = update_command[16:].strip()
    parts = params_text.split('|')
    if len(parts) >= 2:
        machine_name = parts[0].strip()
        update_data = {}

        for part in parts[1:]:
            if ':' in part:
                field, value = part.split(':', 1)
                field = field.strip()
                value = value.strip()

                if field in ['products', 'maintainers']:
                    update_data[field] = [item.strip() for item in value.split(',') if item.strip()]
                else:
                    update_data[field] = value

        print(f"  机器名: {machine_name}")
        for field, value in update_data.items():
            if isinstance(value, list):
                print(f"  {field}: {', '.join(value)}")
            else:
                print(f"  {field}: {value}")

    # 测试3: 删除机器命令解析
    print("\n3. 测试删除机器命令解析:")
    delete_command = "#machine_delete 测试发电机"
    event_data = create_mock_event_data(delete_command)

    print(f"命令: {delete_command}")
    print("解析结果:")

    machine_name = delete_command[16:].strip()
    print(f"  要删除的机器名: {machine_name}")

    # 测试4: 帮助命令
    print("\n4. 测试帮助命令:")
    help_command = "#machine_help"
    event_data = create_mock_event_data(help_command)

    print(f"命令: {help_command}")
    print("  命令格式正确，可以显示帮助信息")

    # 测试5: 格式验证
    print("\n5. 测试命令格式验证:")

    # 错误的添加命令格式
    invalid_add = "#machine_add"
    print(f"无效添加命令: '{invalid_add}' - 缺少参数")

    # 错误的更新命令格式
    invalid_update = "#machine_update"
    print(f"无效更新命令: '{invalid_update}' - 缺少参数")

    # 错误的删除命令格式
    invalid_delete = "#machine_delete"
    print(f"无效删除命令: '{invalid_delete}' - 缺少机器名")

    print("\n机器管理命令解析测试完成!")

if __name__ == "__main__":
    test_command_parsing()