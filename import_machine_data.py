#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器数据导入脚本
将CSV文件中的机器数据导入本地SQLite数据库
"""

import os
import sys
from services.database_manager import DatabaseManager

def main():
    # CSV文件路径
    csv_path = "reference/机器 248a62a2edb380d89c58f242e2ee1db5_all.csv"

    # 检查CSV文件是否存在
    if not os.path.exists(csv_path):
        print(f"错误：找不到CSV文件 {csv_path}")
        print("请确保CSV文件位于reference目录下")
        sys.exit(1)

    print(f"开始导入机器数据从 {csv_path}...")

    # 创建数据库管理器实例
    db_manager = DatabaseManager()

    # 导入数据
    success = db_manager.import_from_csv(csv_path)

    if success:
        print("数据导入成功！")

        # 显示一些统计信息
        print("\n数据统计：")
        regions = db_manager.list_all_regions()
        products = db_manager.list_all_products()

        print(f"地域数量: {len(regions)}")
        print(f"产物数量: {len(products)}")

        # 测试查询功能
        print("\n测试查询功能：")
        test_products = ["雪块", "骨粉", "铁锭"]
        for product in test_products:
            machines = db_manager.search_machines_by_product(product)
            print(f"'{product}' 相关机器数量: {len(machines)}")
            if machines:
                print(f"  示例机器: {machines[0]['name']}")

    else:
        print("数据导入失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()