#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试机器编辑功能
验证添加、更新、删除机器功能是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.machine_manager import MachineManager
from services.database_manager import DatabaseManager

def test_machine_edit_functions():
    """测试机器编辑功能"""
    print("开始测试机器编辑功能...")

    manager = MachineManager()
    db_manager = DatabaseManager()

    # 测试数据
    test_machine_data = {
        'name': '测试机器_编辑功能',
        'region': '测试区',
        'dimension': 'overworld',
        'coordinates': '100, 200, 300',
        'products': ['铁锭', '铜锭'],
        'maintainers': ['测试维护者']
    }

    # 测试1: 添加机器
    print("\n1. 测试添加机器:")
    success = manager.add_machine(test_machine_data)
    print(f"添加机器结果: {'成功' if success else '失败'}")

    if success:
        # 验证机器是否添加成功
        machine_details = manager.get_machine_details(test_machine_data['name'])
        if machine_details:
            print("  验证添加结果:")
            print(f"  机器名: {machine_details['name']}")
            print(f"  地域: {machine_details['region']}")
            print(f"  产物: {', '.join(machine_details['products'])}")
            print(f"  维护者: {', '.join(machine_details['maintainers'])}")
        else:
            print("  验证失败: 无法获取刚添加的机器信息")

    # 测试2: 更新机器
    print("\n2. 测试更新机器:")
    update_data = {
        'region': '新测试区',
        'products': ['铁锭', '金锭', '钻石'],
        'coordinates': '150, 250, 350'
    }

    success = manager.update_machine_by_name(test_machine_data['name'], update_data)
    print(f"更新机器结果: {'成功' if success else '失败'}")

    if success:
        # 验证更新结果
        updated_machine = manager.get_machine_details(test_machine_data['name'])
        if updated_machine:
            print("  验证更新结果:")
            print(f"  新地域: {updated_machine['region']}")
            print(f"  新产物: {', '.join(updated_machine['products'])}")
            print(f"  新坐标: {updated_machine['coordinates']}")

    # 测试3: 删除机器
    print("\n3. 测试删除机器:")
    success = manager.delete_machine_by_name(test_machine_data['name'])
    print(f"删除机器结果: {'成功' if success else '失败'}")

    if success:
        # 验证删除结果
        deleted_machine = manager.get_machine_details(test_machine_data['name'])
        if deleted_machine:
            print("  验证失败: 删除后仍能找到机器")
        else:
            print("  验证成功: 机器已被删除")

    # 测试4: 测试边界情况
    print("\n4. 测试边界情况:")

    # 测试添加重复机器（应该失败）
    duplicate_machine = {
        'name': '测试机器_重复',
        'region': '测试区',
        'dimension': 'overworld',
        'coordinates': '100, 200, 300'
    }

    success1 = manager.add_machine(duplicate_machine)
    print(f"第一次添加 '{duplicate_machine['name']}': {'成功' if success1 else '失败'}")

    # 再次添加相同机器（根据复合约束，应该会失败）
    duplicate_machine['coordinates'] = '101, 201, 301'  # 改变坐标
    success2 = manager.add_machine(duplicate_machine)
    print(f"第二次添加 '{duplicate_machine['name']}': {'成功' if success2 else '失败'}")

    # 清理测试数据
    if success1:
        manager.delete_machine_by_name(duplicate_machine['name'])

    print("\n机器编辑功能测试完成!")

if __name__ == "__main__":
    test_machine_edit_functions()