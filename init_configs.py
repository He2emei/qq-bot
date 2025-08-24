#!/usr/bin/env python3
# init_configs.py - 初始化敏感配置文件
"""
初始化敏感配置文件脚本

此脚本用于初始化项目中的敏感配置文件，避免将敏感信息提交到git仓库。
运行此脚本将创建必要的配置文件模板，用户需要手动填写敏感信息。
"""

import os
import sys
import json
from config_manager import init_all_configs, config_manager

def create_config_template():
    """创建配置文件模板"""
    print("🚀 开始初始化敏感配置文件...")

    # 初始化所有配置文件
    success = init_all_configs()

    if success:
        print("✅ 所有配置文件已成功初始化！")
        print("\n📋 接下来您需要：")
        print("1. 编辑 data/authenticatorList.json - 添加您的验证器信息")
        print("2. 编辑 data/code.json - 添加您的验证码映射")
        print("3. 编辑 data/ze_account.json - 添加您的ZE账户信息")
        print("4. 编辑 data/yqm.json - 添加您的邀请码列表（可选）")
        print("5. data/memory.json 已自动初始化为空配置")
        print("\n⚠️  重要提醒：")
        print("- 这些文件已被 .gitignore 排除，不会提交到git")
        print("- 请妥善保管这些文件，不要分享给他人")
        print("- 如果在服务器上使用，建议定期备份这些配置")
    else:
        print("❌ 配置文件初始化失败！")
        return False

    return True

def show_config_status():
    """显示配置文件状态"""
    print("\n📊 配置文件状态：")
    status = config_manager.list_config_status()

    for config_type, exists in status.items():
        status_icon = "✅" if exists else "❌"
        file_path = f"data/{config_manager.sensitive_configs[config_type]}"
        print(f"  {status_icon} {config_type}: {file_path}")

def backup_configs():
    """备份现有配置文件"""
    print("\n💾 备份现有配置文件...")
    from config_manager import backup_all_configs

    if backup_all_configs():
        print("✅ 备份完成！")
        print("备份文件保存在原配置文件同目录，扩展名为 .backup")
    else:
        print("❌ 备份失败！")

def import_qbot_configs():
    """导入QBot配置文件"""
    from config_manager import import_all_qbot_configs

    print("\n[INFO] 从QBot导入配置文件...")

    if import_all_qbot_configs():
        print("[SUCCESS] QBot配置导入成功！")
    else:
        print("[ERROR] QBot配置导入失败！")

def main():
    """主函数"""
    print("QQ Bot 敏感配置文件初始化工具")
    print("=" * 50)

    # 检查参数
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action == "backup":
            backup_configs()
            return
        elif action == "status":
            show_config_status()
            return
        elif action == "import":
            import_qbot_configs()
            return
        elif action == "import_ze":
            from config_manager import import_specific_qbot_config
            print("\n[INFO] 导入QBot ze_account.json配置...")
            if import_specific_qbot_config("QBot", "ze_account"):
                print("[SUCCESS] ze_account.json 导入成功！")
            else:
                print("[ERROR] ze_account.json 导入失败！")
            return

    # 显示当前状态
    show_config_status()

    # 显示可用选项
    print("\n[INFO] 可用操作:")
    print("1. 初始化默认配置 (直接回车)")
    print("2. 导入QBot配置: python init_configs.py import")
    print("3. 仅导入ze_account: python init_configs.py import_ze")
    print("4. 查看状态: python init_configs.py status")
    print("5. 备份配置: python init_configs.py backup")

    # 确认操作
    print("\n[WARNING] 此操作将创建/覆盖敏感配置文件。")
    confirm = input("是否继续？(y/N): ").strip().lower()

    if confirm in ['y', 'yes']:
        if create_config_template():
            show_config_status()
    else:
        print("操作已取消。")

if __name__ == "__main__":
    main()