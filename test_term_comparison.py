#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对比当前代码与Notion-Tools项目的学期系统
"""

def test_current_term_system():
    """测试当前代码的学期系统"""
    print("=== 测试当前代码的学期系统 ===")
    try:
        from utils.notion_utils import get_term, get_week_num, wk_name

        print("1. 获取当前学期...")
        current_term = get_term()
        print(f"   当前学期: {current_term}")

        if current_term:
            print("2. 计算当前周数...")
            week_num = get_week_num()
            print(f"   当前周数: {week_num}")

            print("3. 生成周页面名称...")
            week_name = wk_name()
            print(f"   周页面名称: {week_name}")

            return {
                'success': True,
                'term': current_term,
                'week_num': week_num,
                'week_name': week_name
            }
        else:
            print("   未能获取到当前学期")
            return {'success': False, 'error': 'No current term found'}

    except Exception as e:
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def test_notion_tools_term_system():
    """测试Notion-Tools项目的学期系统"""
    print("\n=== 测试Notion-Tools项目的学期系统 ===")
    try:
        # 切换到notion_tools_backup目录并添加路径
        import sys
        import os
        original_cwd = os.getcwd()
        backup_dir = os.path.join(original_cwd, 'notion_tools_backup')
        os.chdir(backup_dir)
        sys.path.insert(0, backup_dir)

        from src.sub_operation import get_term, get_week_num, wk_name

        print("1. 获取当前学期...")
        current_term = get_term()
        print(f"   当前学期: {current_term}")

        if current_term:
            print("2. 计算当前周数...")
            week_num = get_week_num()
            print(f"   当前周数: {week_num}")

            print("3. 生成周页面名称...")
            week_name = wk_name()
            print(f"   周页面名称: {week_name}")

            # 恢复原始工作目录
            os.chdir(original_cwd)

            return {
                'success': True,
                'term': current_term,
                'week_num': week_num,
                'week_name': week_name
            }
        else:
            print("   未能获取到当前学期")
            os.chdir(original_cwd)
            return {'success': False, 'error': 'No current term found'}

    except Exception as e:
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        # 确保恢复工作目录
        try:
            os.chdir(original_cwd)
        except:
            pass
        return {'success': False, 'error': str(e)}


def compare_results(current_result, notion_tools_result):
    """比较两个系统的结果"""
    print("\n=== 结果对比 ===")

    if not current_result['success'] and not notion_tools_result['success']:
        print("❌ 两个系统都失败了")
        print(f"当前系统错误: {current_result.get('error', 'Unknown')}")
        print(f"Notion-Tools错误: {notion_tools_result.get('error', 'Unknown')}")
        return

    if current_result['success'] and not notion_tools_result['success']:
        print("✅ 当前系统成功，Notion-Tools系统失败")
        print("当前系统结果:", current_result)
        return

    if not current_result['success'] and notion_tools_result['success']:
        print("❌ 当前系统失败，Notion-Tools系统成功")
        print("需要修复当前系统以匹配Notion-Tools的功能")
        return

    # 两个系统都成功，对比结果
    print("✅ 两个系统都成功运行")

    # 对比学期信息
    current_term = current_result.get('term', {})
    notion_term = notion_tools_result.get('term', {})

    print(f"当前系统学期: {current_term.get('name', 'N/A')}")
    print(f"Notion-Tools学期: {notion_term.get('name', 'N/A')}")

    # 对比周数
    current_week = current_result.get('week_num', 0)
    notion_week = notion_tools_result.get('week_num', 0)
    print(f"当前系统周数: {current_week}")
    print(f"Notion-Tools周数: {notion_week}")

    # 对比周名称
    current_name = current_result.get('week_name', '')
    notion_name = notion_tools_result.get('week_name', '')
    print(f"当前系统周名称: {current_name}")
    print(f"Notion-Tools周名称: {notion_name}")

    if current_week == notion_week and current_name == notion_name:
        print("✅ 结果完全一致")
    else:
        print("⚠️ 结果存在差异，需要进一步调查")


def main():
    """主函数"""
    print("开始对比学期系统...")

    # 测试当前系统
    current_result = test_current_term_system()

    # 测试Notion-Tools系统
    notion_tools_result = test_notion_tools_term_system()

    # 对比结果
    compare_results(current_result, notion_tools_result)

    print("\n对比完成。")


if __name__ == "__main__":
    main()