#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重复名称机器的处理
验证两个刷雪机都能正确存在
"""

from services.machine_manager import MachineManager

def test_duplicate_machines():
    """测试重复名称机器的处理"""
    manager = MachineManager()

    print("测试重复名称机器的处理...")

    # 测试1: 按产物查询雪块，应该找到两个刷雪机
    print("\n1. 测试按产物查询 '雪块':")
    machines = manager.search_machines_by_product("雪块")

    print(f"找到 {len(machines)} 台生产雪块的机器")
    for i, machine in enumerate(machines, 1):
        print(f"{i}. {machine['name']}")
        print(f"   地域: {machine['region']}")
        print(f"   坐标: {machine['coordinates']}")
        print(f"   维度: {machine['dimension']}")
        print()

    # 测试2: 按地域查询樱岭，应该找到刷雪机
    print("\n2. 测试按地域查询 '樱岭':")
    machines = manager.search_machines_by_region("樱岭")

    print(f"找到 {len(machines)} 台樱岭地域的机器")
    for i, machine in enumerate(machines, 1):
        print(f"{i}. {machine['name']}")
        print(f"   产物: {', '.join(machine['products'])}")
        print(f"   坐标: {machine['coordinates']}")
        print()

    # 测试3: 按地域查询思源市，应该找到刷雪机
    print("\n3. 测试按地域查询 '思源市':")
    machines = manager.search_machines_by_region("思源市")

    print(f"找到 {len(machines)} 台思源市地域的机器")
    for i, machine in enumerate(machines, 1):
        print(f"{i}. {machine['name']}")
        print(f"   产物: {', '.join(machine['products'])}")
        print(f"   坐标: {machine['coordinates']}")
        print()

if __name__ == "__main__":
    test_duplicate_machines()