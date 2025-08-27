#!/usr/bin/env python3
# test_machine_debug.py - 调试机器管理器

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """测试基本导入"""
    print("Testing basic imports...")

    try:
        import config
        print("[OK] config imported")

        from services.notion_service import notion_service
        print("[OK] notion_service imported")

        from services.machine_manager import machine_manager
        print("[OK] machine_manager imported")

        print("All imports successful!")
        return True

    except Exception as e:
        import traceback
        print(f"[ERROR] Import error: {e}")
        print(traceback.format_exc())
        return False

def test_notion_config():
    """测试Notion配置"""
    print("\nTesting Notion configuration...")

    try:
        import config
        print(f"✓ NOTION_TOKEN: {config.NOTION_TOKEN[:20]}...")
        print(f"✓ NOTION_VERSION: {config.NOTION_VERSION}")
        print(f"✓ Machines DB ID: {config.NOTION_DATABASES.get('machines', 'Not found')}")

        return True

    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

def test_notion_connection():
    """测试Notion连接"""
    print("\nTesting Notion API connection...")

    try:
        from services.notion_service import notion_service

        print(f"Base URL: {notion_service.base_url}")
        print(f"Version: {notion_service.headers.get('notion-version', 'Not found')}")

        # 测试数据库查询
        database_id = '248a62a2edb380dca1d3ef665efc5d73'
        url = f"{notion_service.base_url}databases/{database_id}/query/"

        print(f"Querying database: {database_id}")
        response = notion_service.session.post(url, headers=notion_service.headers, json={})

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✓ Query successful! Found {len(results)} items")
            return True
        else:
            print(f"✗ Query failed: {response.text[:200]}")
            return False

    except Exception as e:
        import traceback
        print(f"✗ Connection error: {e}")
        print(traceback.format_exc())
        return False

def test_machine_manager():
    """测试机器管理器"""
    print("\nTesting machine manager...")

    try:
        from services.machine_manager import machine_manager

        # 测试地域列表
        print("Testing list_all_regions...")
        regions = machine_manager.list_all_regions()
        print(f"✓ Found regions: {regions}")

        # 测试产物列表
        print("Testing list_all_products...")
        products = machine_manager.list_all_products()
        print(f"✓ Found products: {products[:3]}... (showing first 3)")

        return True

    except Exception as e:
        import traceback
        print(f"✗ Machine manager error: {e}")
        print(traceback.format_exc())
        return False

def main():
    """主函数"""
    print("Machine Manager Debug Tool")
    print("=" * 50)

    tests = [
        ("基本导入测试", test_basic_imports),
        ("Notion配置测试", test_notion_config),
        ("Notion连接测试", test_notion_connection),
        ("机器管理器测试", test_machine_manager),
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
    print("\n📊 测试结果总结")
    print("=" * 30)

    all_passed = True
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n🎉 所有测试通过！机器管理器工作正常。")
    else:
        print("\n❌ 部分测试失败，请检查配置和网络连接。")

if __name__ == "__main__":
    main()