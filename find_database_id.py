#!/usr/bin/env python3
# find_database_id.py - 查找Notion数据库ID

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from services.notion_service import notion_service

def find_databases():
    """查找用户可访问的所有数据库"""
    print("Searching for all accessible databases...")

    # 使用Notion搜索API查找所有数据库
    url = f"{notion_service.base_url}search"

    payload = {
        "query": "",
        "filter": {
            "value": "database",
            "property": "object"
        },
        "sort": {
            "direction": "ascending",
            "timestamp": "last_edited_time"
        }
    }

    try:
        response = requests.post(url, headers=notion_service.headers, json=payload, verify=False, proxies=notion_service.session.proxies)
        print(f"Search Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            print(f"\nFound {len(results)} databases:")
            print("-" * 50)

            for i, db in enumerate(results, 1):
                # 解析数据库标题
                title = "Untitled"
                if db.get('title'):
                    title_items = db['title']
                    if title_items:
                        title = title_items[0].get('plain_text', 'Untitled')

                database_id = db.get('id', 'Unknown')
                created_time = db.get('created_time', 'Unknown')[:10]
                last_edited = db.get('last_edited_time', 'Unknown')[:10]

                print(f"{i}. {title}")
                print(f"   ID: {database_id}")
                print(f"   Created: {created_time}")
                print(f"   Last Edited: {last_edited}")
                print()

            if results:
                print("To use one of these databases, copy the ID and update config.py:")
                print("NOTION_DATABASES = {")
                print("    'machines': 'PASTE_DATABASE_ID_HERE'")
                print("}")
            else:
                print("No databases found. Make sure:")
                print("1. Your integration has database access permissions")
                print("2. The integration is shared with the databases")
                print("3. The databases are not in a private workspace")

        else:
            print(f"Search failed: {response.text}")

    except Exception as e:
        print(f"Search error: {e}")

def test_specific_id(database_id):
    """测试特定的数据库ID"""
    print(f"\nTesting specific database ID: {database_id}")

    url = f"https://api.notion.com/v1/databases/{database_id}"

    try:
        response = requests.get(url, headers=notion_service.headers, verify=False, proxies=notion_service.session.proxies)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            title = "Untitled"
            if data.get('title'):
                title_items = data['title']
                if title_items:
                    title = title_items[0].get('plain_text', 'Untitled')

            print(f"SUCCESS: Database '{title}' is accessible!")
            print(f"Full ID: {database_id}")
            return True
        else:
            print(f"FAILED: {response.text}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """主函数"""
    print("Notion Database ID Finder")
    print("=" * 30)

    if len(sys.argv) > 1:
        # 测试特定的ID
        database_id = sys.argv[1]
        test_specific_id(database_id)
    else:
        # 查找所有数据库
        find_databases()

if __name__ == "__main__":
    main()