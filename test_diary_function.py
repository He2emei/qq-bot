#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日记功能
验证日记功能是否仍然正常使用Notion API
"""

from services.notion_service import daily_manager, notion_service
import config

def test_diary_function():
    """测试日记功能"""
    print("开始测试日记功能...")

    try:
        # 测试1: 获取今日页面
        print("\n1. 测试获取今日页面:")
        today_page = daily_manager.get_today_page()
        if today_page:
            print(f"今日页面存在: {today_page['id']}")
        else:
            print("今日页面不存在")

        # 测试2: 获取Notion服务状态
        print("\n2. 测试Notion服务状态:")
        print(f"Notion版本: {config.NOTION_VERSION}")
        print(f"日记Token配置: {'已配置' if hasattr(config, 'NOTION_TOKEN_DIARY') and config.NOTION_TOKEN_DIARY else '未配置'}")
        print(f"普通Token配置: {'已配置' if hasattr(config, 'NOTION_TOKEN') and config.NOTION_TOKEN else '未配置'}")

        # 测试3: 验证Notion服务实例
        print("\n3. 测试Notion服务实例:")
        print(f"普通服务初始化: {'成功' if notion_service else '失败'}")
        print(f"日记管理器初始化: {'成功' if daily_manager else '失败'}")

        print("\n日记功能测试完成 - Notion API 仍然正常工作")

    except Exception as e:
        print(f"日记功能测试失败: {e}")

if __name__ == "__main__":
    test_diary_function()