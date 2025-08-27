#!/usr/bin/env python3
# debug_notion.py - 调试Notion API连接

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from services.notion_service import notion_service

def test_basic_connection():
    """测试基础连接"""
    print("Testing basic connection to Notion API...")

    url = "https://api.notion.com/v1/users/me"
    headers = notion_service.headers

    print(headers)

    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Basic connection successful!")
            return True
        else:
            print(f"✗ Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def test_database_access():
    """测试数据库访问"""
    print("\nTesting database access...")

    database_id = "248a62a2edb380dca1d3ef665efc5d73"
    url = f"https://api.notion.com/v1/databases/{database_id}"

    try:
        response = requests.get(url, headers=notion_service.headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✓ Database access successful!")
            print(f"Database title: {data.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            return True
        else:
            print(f"✗ Database access failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Database access error: {e}")
        return False

def test_database_query():
    """测试数据库查询"""
    print("\nTesting database query...")

    database_id = "248a62a2edb380d89c58f242e2ee1db5"
    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    try:
        response = requests.post(url, headers=notion_service.headers, json={})
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✓ Query successful! Found {len(results)} items")

            # 显示前几个结果的基本信息
            for i, item in enumerate(results[:3]):
                props = item.get('properties', {})
                name_prop = props.get('Name', {}).get('title', [])
                name = name_prop[0].get('plain_text', 'Unknown') if name_prop else 'Unknown'
                print(f"  Item {i+1}: {name}")
            return True
        else:
            print(f"✗ Query failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Query error: {e}")
        return False

def main():
    """主函数"""
    print("Notion API Debug Tool")
    print("=" * 50)

    tests = [
        ("基础连接测试", test_basic_connection),
        ("数据库访问测试", test_database_access),
        ("数据库查询测试", test_database_query)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))

    print("\n[SUMMARY] Test Results")
    print("=" * 30)

    for test_name, result in results:
        status = "[PASS] " if result else "[FAIL] "
        print(f"{status} {test_name}")

if __name__ == "__main__":
    main()