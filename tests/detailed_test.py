#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from services.notion_service import notion_service

print("Detailed Notion API Test")
print("=" * 30)

# 1. 测试数据库访问
print("\n1. Testing database access...")
database_id = "248a62a2-edb3-80d8-9c58-f242e2ee1db5"
url = f"https://api.notion.com/v1/databases/{database_id}"

try:
    response = requests.get(url, headers=notion_service.headers, verify=False, proxies=notion_service.session.proxies)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("Database info:")
        print(f"  Title: {data.get('title', [{}])[0].get('plain_text', 'Unknown')}")
        print(f"  Properties: {list(data.get('properties', {}).keys())}")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Exception: {e}")

# 2. 测试简单查询
print("\n2. Testing simple query...")
query_url = f"https://api.notion.com/v1/databases/{database_id}/query"

try:
    response = requests.post(query_url, headers=notion_service.headers, json={}, verify=False, proxies=notion_service.session.proxies)
    print(f"Query Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"SUCCESS: Found {len(results)} items")

        if results:
            # 显示第一个项目的详细信息
            first_item = results[0]
            print("First item details:")
            print(f"  ID: {first_item.get('id')}")
            properties = first_item.get('properties', {})
            for prop_name, prop_data in properties.items():
                if prop_data.get('title'):
                    title_items = prop_data['title']
                    if title_items:
                        print(f"  {prop_name}: {title_items[0].get('plain_text', 'N/A')}")
                elif prop_data.get('select'):
                    print(f"  {prop_name}: {prop_data['select'].get('name', 'N/A')}")
                elif prop_data.get('rich_text'):
                    text_items = prop_data['rich_text']
                    if text_items:
                        print(f"  {prop_name}: {text_items[0].get('plain_text', 'N/A')}")
                elif prop_data.get('multi_select'):
                    items = [item.get('name', '') for item in prop_data['multi_select']]
                    print(f"  {prop_name}: {items}")
                else:
                    print(f"  {prop_name}: {type(prop_data)}")
    else:
        print(f"Query failed: {response.text}")

except Exception as e:
    print(f"Query exception: {e}")
    import traceback
    print(traceback.format_exc())

print("\nTest completed.")