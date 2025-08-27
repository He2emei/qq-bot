#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from services.notion_service import notion_service

print("Testing Notion Database Access...")
try:
    # 测试数据库访问
    database_id = "248a62a2edb380dca1d3ef665efc5d73"
    url = f"https://api.notion.com/v1/databases/{database_id}"

    response = requests.get(url, headers=notion_service.headers, proxies=notion_service.session.proxies, verify=False)
    print(f"Database Access Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        title = data.get('title', [{}])[0].get('plain_text', 'Unknown')
        print(f"SUCCESS: Database '{title}' accessed successfully!")
    else:
        print(f"ERROR: {response.text}")

    # 测试数据库查询
    print("\nTesting Database Query...")
    query_url = f"https://api.notion.com/v1/databases/{database_id}/query"
    response = requests.post(query_url, headers=notion_service.headers, json={}, proxies=notion_service.session.proxies, verify=False)

    print(f"Query Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"SUCCESS: Query returned {len(results)} items")

        # 显示前几个项目
        for i, item in enumerate(results[:3]):
            props = item.get('properties', {})
            name_prop = props.get('Name', {}).get('title', [])
            name = name_prop[0].get('plain_text', 'Unknown') if name_prop else 'Unknown'
            print(f"  Item {i+1}: {name}")
    else:
        print(f"ERROR: {response.text}")

except Exception as e:
    print(f"EXCEPTION: {e}")