#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Notion 功能集成
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from services.notion_service import notion_service, daily_manager
from utils.notion_utils import get_bing_image_url, process_notion_blocks
import json


def test_notion_connection():
    """测试 Notion API 连接"""
    print("=== 测试 Notion API 连接 ===")

    try:
        # 测试查询数据库
        result = notion_service.query_database("Daily Dairy 2.0")
        print(f"✅ 连接成功，找到 {len(result.get('results', []))} 个页面")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_daily_manager():
    """测试每日管理器"""
    print("\n=== 测试每日管理器 ===")

    try:
        # 获取今日日期
        today_date = daily_manager.get_today_date()
        print(f"✅ 今日日期: {today_date}")

        # 格式化日期
        date_str = daily_manager.date_dt2nt(today_date)
        print(f"✅ Notion 日期格式: {date_str}")

        # 获取今日页面（如果存在）
        today_page = daily_manager.get_today_page()
        if today_page:
            print(f"✅ 今日页面已存在: {today_page['id']}")
        else:
            print("ℹ️ 今日页面不存在")

        return True
    except Exception as e:
        print(f"❌ 每日管理器测试失败: {e}")
        return False


def test_bing_image():
    """测试 Bing 图片获取"""
    print("\n=== 测试 Bing 图片获取 ===")

    try:
        image_url = get_bing_image_url()
        print(f"✅ Bing 图片 URL: {image_url}")
        return True
    except Exception as e:
        print(f"❌ Bing 图片获取失败: {e}")
        return False


def test_template_loading():
    """测试模板加载"""
    print("\n=== 测试模板加载 ===")

    try:
        from utils.notion_utils import load_template
        template = load_template("daily_template")
        print("✅ 模板加载成功")
        print(f"模板结构: {json.dumps(template, indent=2, ensure_ascii=False)[:200]}...")
        return True
    except Exception as e:
        print(f"❌ 模板加载失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 开始测试 Notion 功能集成\n")

    results = []

    # 执行各项测试
    results.append(("Notion API 连接", test_notion_connection()))
    results.append(("每日管理器", test_daily_manager()))
    results.append(("Bing 图片获取", test_bing_image()))
    results.append(("模板加载", test_template_loading()))

    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n=== 测试结果汇总 ===")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n📊 通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 所有测试通过！Notion 功能已成功集成。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查配置和网络连接。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)