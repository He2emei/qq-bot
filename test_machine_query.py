#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试机器查询功能
验证本地数据库查询是否正常工作
"""

from services.machine_manager import MachineManager

def test_machine_queries():
    """测试机器查询功能"""
    manager = MachineManager()

    print("开始测试机器查询功能...")

    # 测试1: 按产物查询
    print("\n1. 按产物查询测试:")
    test_products = ["雪块", "骨粉", "铁锭", "圆石"]

    for product in test_products:
        machines = manager.search_machines_by_product(product)
        print(f"'{product}' 相关机器数量: {len(machines)}")
        if machines:
            print(f"  示例机器: {machines[0]['name']}")
            print(f"  地域: {machines[0]['region']}")
            print(f"  坐标: {machines[0]['coordinates']}")

    # 测试2: 按地域查询
    print("\n2. 按地域查询测试:")
    test_regions = ["樱岭", "江都市", "幻想乡"]

    for region in test_regions:
        machines = manager.search_machines_by_region(region)
        print(f"'{region}' 地域机器数量: {len(machines)}")
        if machines:
            print(f"  示例机器: {machines[0]['name']}")
            print(f"  产物: {', '.join(machines[0]['products'][:2])}")  # 只显示前2个产物

    # 测试3: 获取机器详情
    print("\n3. 获取机器详情测试:")
    test_machine_names = ["刷雪机", "五合一农业机", "320熔炉组"]

    for machine_name in test_machine_names:
        details = manager.get_machine_details(machine_name)
        if details:
            print(f"机器: {details['name']}")
            print(f"  地域: {details['region']}")
            print(f"  产物: {', '.join(details['products'])}")
            print(f"  维护者: {', '.join(details['maintainers']) if details['maintainers'] else '无'}")
            print(f"  坐标: {details['coordinates']}")
        else:
            print(f"未找到机器: {machine_name}")

    # 测试4: 获取列表
    print("\n4. 获取列表测试:")
    regions = manager.list_all_regions()
    products = manager.list_all_products()

    print(f"地域总数: {len(regions)}")
    print(f"产物总数: {len(products)}")
    print(f"地域示例: {', '.join(regions[:3])}")
    print(f"产物示例: {', '.join(products[:3])}")

if __name__ == "__main__":
    test_machine_queries()