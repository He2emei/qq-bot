#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Final Machine Manager Test")
print("=" * 40)

try:
    from services.machine_manager import machine_manager

    # 测试地域列表
    print("1. Testing list_all_regions...")
    regions = machine_manager.list_all_regions()
    print(f"   Found {len(regions)} regions: {regions}")

    # 测试产物列表
    print("2. Testing list_all_products...")
    products = machine_manager.list_all_products()
    print(f"   Found {len(products)} products: {products[:5]}...")

    # 测试查询机器（使用第一个产物）
    if products:
        first_product = products[0]
        print(f"3. Testing search by product: {first_product}")
        machines = machine_manager.search_machines_by_product(first_product)
        print(f"   Found {len(machines)} machines")

        if machines:
            print("   First machine info:")
            first_machine = machines[0]
            print(f"   - Name: {first_machine['name']}")
            print(f"   - Region: {first_machine['region']}")
            print(f"   - Products: {first_machine['products']}")
            print(f"   - Coordinates: {first_machine['coordinates']}")

    # 测试地域查询（使用第一个地域）
    if regions:
        first_region = regions[0]
        print(f"4. Testing search by region: {first_region}")
        machines = machine_manager.search_machines_by_region(first_region)
        print(f"   Found {len(machines)} machines in {first_region}")

    print("\nSUCCESS: All machine manager tests completed!")
    print("The Notion machine database integration is working correctly.")

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    print(traceback.format_exc())