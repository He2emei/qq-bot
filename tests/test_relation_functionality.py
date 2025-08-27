#!/usr/bin/env python3
# test_relation_functionality.py - 测试relation功能

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_relation_imports():
    """测试relation功能的导入"""
    print("Testing relation functionality imports...")

    try:
        import config
        print("[OK] config imported")

        from services.notion_service import notion_service
        print("[OK] notion_service imported")

        from services.machine_manager import machine_manager
        print("[OK] machine_manager imported")

        print("All relation imports successful!")
        return True

    except Exception as e:
        import traceback
        print(f"[ERROR] Import error: {e}")
        print(traceback.format_exc())
        return False

def test_database_config():
    """测试数据库配置"""
    print("\nTesting database configuration...")

    try:
        import config

        databases = config.NOTION_DATABASES
        required_dbs = ['machines', 'products', 'regions']

        for db_name in required_dbs:
            if db_name in databases:
                db_id = databases[db_name]
                print(f"[OK] {db_name}: {db_id}")
            else:
                print(f"[ERROR] Missing database: {db_name}")
                return False

        return True

    except Exception as e:
        print(f"[ERROR] Config test error: {e}")
        return False

def test_relation_queries():
    """测试relation查询功能"""
    print("\nTesting relation queries...")

    try:
        from services.machine_manager import machine_manager

        # 测试获取地域列表
        print("Testing list_all_regions...")
        regions = machine_manager.list_all_regions()
        print(f"[OK] Found {len(regions)} regions: {regions[:5]}...")

        # 测试获取产物列表
        print("Testing list_all_products...")
        products = machine_manager.list_all_products()
        print(f"[OK] Found {len(products)} products: {products[:5]}...")

        # 测试按地域查询机器（如果有地域数据）
        if regions:
            test_region = regions[0]
            print(f"Testing search_machines_by_region with '{test_region}'...")
            machines_by_region = machine_manager.search_machines_by_region(test_region)
            print(f"[OK] Found {len(machines_by_region)} machines in region '{test_region}'")

        # 测试按产物查询机器（如果有产物数据）
        if products:
            test_product = products[0]
            print(f"Testing search_machines_by_product with '{test_product}'...")
            machines_by_product = machine_manager.search_machines_by_product(test_product)
            print(f"[OK] Found {len(machines_by_product)} machines producing '{test_product}'")

        return True

    except Exception as e:
        import traceback
        print(f"[ERROR] Relation query error: {e}")
        print(traceback.format_exc())
        return False

def main():
    """主函数"""
    print("Relation Functionality Test Tool")
    print("=" * 50)

    tests = [
        ("基础导入测试", test_relation_imports),
        ("数据库配置测试", test_database_config),
        ("Relation查询测试", test_relation_queries),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ 测试执行失败: {e}")
            results.append((test_name, False))

    # 总结
    print("\n[SUMMARY] Test Results Summary")
    print("=" * 30)

    all_passed = True
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n[SUCCESS] All tests passed! Relation functionality is working correctly.")
    else:
        print("\n[ERROR] Some tests failed, please check configuration and database settings.")

if __name__ == "__main__":
    main()