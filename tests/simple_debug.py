#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from services.notion_service import notion_service

print("Testing Notion API basic connection...")
try:
    url = "https://api.notion.com/v1/users/me"
    headers = {
        "Authorization": f"Bearer {notion_service.headers['Authorization'].split(' ')[1]}",
        "Notion-Version": notion_service.headers["notion-version"]
    }

    print(headers)

    response = requests.get(url, headers=headers, proxies=notion_service.session.proxies)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("SUCCESS: Basic connection to Notion API works!")
        print("The proxy configuration is working correctly.")
    else:
        print(f"ERROR: {response.text}")

except Exception as e:
    print(f"EXCEPTION: {e}")