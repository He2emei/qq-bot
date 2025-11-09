#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试Notion-Tools项目的学期系统
"""

import sys
import os

# 添加notion_tools_backup到路径
sys.path.insert(0, 'notion_tools_backup')

def test_notion_tools_simple():
    """简单测试Notion-Tools的学期系统"""
    print("=" * 60)
    print("测试Notion-Tools项目的学期系统")
    print("=" * 60)

    try:
        from src.sub_operation import get_term, get_week_num, wk_name

        print("正在获取当前学期...")
        current_term = get_term()
        print(f'当前学期: {current_term}')

        if current_term:
            print("正在计算当前周数...")
            week_num = get_week_num()
            print(f'当前周数: {week_num}')

            print("正在生成周页面名称...")
            week_name = wk_name()
            print(f'周页面名称: {week_name}')

            print("✓ Notion-Tools项目学期系统测试完成")
        else:
            print("✗ 未找到当前学期")

    except Exception as e:
        print(f"✗ Notion-Tools项目测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_notion_tools_simple()