#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Notion-Tools项目的学期系统
"""

import sys
import os
sys.path.append('.')

def test_current_project():
    """测试当前项目的学期系统"""
    print("=" * 50)
    print("测试当前项目的学期系统")
    print("=" * 50)

    try:
        from utils.notion_utils import get_term, get_week_num, wk_name

        print("正在获取当前学期...")
        current_term = get_term()
        print(f'当前学期: {current_term}')

        print("正在计算当前周数...")
        week_num = get_week_num()
        print(f'当前周数: {week_num}')

        print("正在生成周页面名称...")
        week_name = wk_name()
        print(f'周页面名称: {week_name}')

        print("✓ 当前项目学期系统测试完成")

    except Exception as e:
        print(f"✗ 当前项目测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_notion_tools():
    """测试Notion-Tools项目的学期系统"""
    print("\n" + "=" * 50)
    print("测试Notion-Tools项目的学期系统")
    print("=" * 50)

    notion_tools_path = r"E:\Project\Notion-Tools"
    if not os.path.exists(notion_tools_path):
        print(f"✗ Notion-Tools路径不存在: {notion_tools_path}")
        return

    try:
        # 添加Notion-Tools路径到sys.path
        sys.path.insert(0, notion_tools_path)

        from src.sub_operation import get_term, get_week_num, wk_name

        print("正在获取当前学期...")
        current_term = get_term()
        print(f'当前学期: {current_term}')

        print("正在计算当前周数...")
        week_num = get_week_num()
        print(f'当前周数: {week_num}')

        print("正在生成周页面名称...")
        week_name = wk_name()
        print(f'周页面名称: {week_name}')

        print("✓ Notion-Tools项目学期系统测试完成")

    except Exception as e:
        print(f"✗ Notion-Tools项目测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_current_project()
    test_notion_tools()
    print("\n" + "=" * 50)
    print("所有测试完成")
    print("=" * 50)