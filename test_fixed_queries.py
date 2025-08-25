#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的机器查询功能
验证字段映射修复是否正确
"""

from services.machine_manager import MachineManager

def test_fixed_queries():
    """测试修复后的查询功能"""
    manager = MachineManager()

    print("测试修复后的查询功能...")

    # 测试1: 按产物查询 - 铁锭
    print("\n1. 测试按产物查询 '铁锭':")
    machines = manager.search_machines_by_product("铁锭")

    for machine in machines:
        print(f"机器: {machine['name']}")
        print(f"  地域: {machine['region']}")
        print(f"  产物: {', '.join(machine['products'])}")
        print(f"  维护者: {', '.join(machine['maintainers']) if machine['maintainers'] else '无'}")
        print(f"  坐标: {machine['coordinates']}")
        print()

    # 测试2: 按地域查询 - 樱岭
    print("\n2. 测试按地域查询 '樱岭':")
    machines = manager.search_machines_by_region("樱岭")

    for machine in machines:
        print(f"机器: {machine['name']}")
        print(f"  产物: {', '.join(machine['products'])}")
        print(f"  坐标: {machine['coordinates']}")
        print()

    # 测试3: 获取机器详情 - 通天塔刷铁机
    print("\n3. 测试获取机器详情 '通天塔刷铁机':")
    details = manager.get_machine_details("通天塔刷铁机")

    if details:
        print(f"机器: {details['name']}")
        print(f"  地域: {details['region']}")
        print(f"  产物: {', '.join(details['products'])}")
        print(f"  维护者: {', '.join(details['maintainers']) if details['maintainers'] else '无'}")
        print(f"  维度: {details['dimension']}")
        print(f"  坐标: {details['coordinates']}")
    else:
        print("未找到机器")

if __name__ == "__main__":
    test_fixed_queries()