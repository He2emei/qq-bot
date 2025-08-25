# services/machine_manager.py
import json
from typing import Dict, Any, List, Optional
from services.database_manager import DatabaseManager
import config

class MachineManager:
    """
    机器数据库管理器

    负责管理本地SQLite数据库中的机器数据，包括：
    - 根据产物查询机器
    - 添加/编辑机器信息
    - 查询机器详细信息
    """

    def __init__(self):
        self.db_manager = DatabaseManager()

    def search_machines_by_product(self, product: str) -> List[Dict[str, Any]]:
        """
        根据产物搜索机器

        Args:
            product: 产物名称

        Returns:
            List[Dict[str, Any]]: 匹配的机器列表
        """
        try:
            return self.db_manager.search_machines_by_product(product)
        except Exception as e:
            print(f"查询机器失败: {e}")
            return []

    # 移除不再需要的方法：_find_product_by_name, _search_machines_by_relation, _get_page_name_by_id
    # 这些方法在本地数据库实现中不再需要

    def search_machines_by_region(self, region: str) -> List[Dict[str, Any]]:
        """
        根据地域搜索机器

        Args:
            region: 地域名称

        Returns:
            List[Dict[str, Any]]: 匹配的机器列表
        """
        try:
            return self.db_manager.search_machines_by_region(region)
        except Exception as e:
            print(f"查询地域机器失败: {e}")
            return []

    # 移除不再需要的方法：_find_region_by_name
    # 这个方法在本地数据库实现中不再需要

    def get_machine_details(self, machine_name: str) -> Optional[Dict[str, Any]]:
        """
        获取机器详细信息

        Args:
            machine_name: 机器名称

        Returns:
            Optional[Dict[str, Any]]: 机器详细信息
        """
        try:
            return self.db_manager.get_machine_details(machine_name)
        except Exception as e:
            print(f"获取机器详情失败: {e}")
            return None

    def list_all_regions(self) -> List[str]:
        """
        获取所有地域列表

        Returns:
            List[str]: 地域名称列表
        """
        try:
            return self.db_manager.list_all_regions()
        except Exception as e:
            print(f"获取地域列表失败: {e}")
            return []

    def list_all_products(self) -> List[str]:
        """
        获取所有产物列表

        Returns:
            List[str]: 产物名称列表
        """
        try:
            return self.db_manager.list_all_products()
        except Exception as e:
            print(f"获取产物列表失败: {e}")
            return []

    # 移除不再需要的方法：_parse_machine_page
    # 本地数据库查询已经返回正确格式的数据

    def add_machine(self, machine_data: Dict[str, Any]) -> bool:
        """
        添加新机器到数据库

        注意：此方法暂未实现本地数据库版本，主要功能已迁移到本地数据库查询

        Args:
            machine_data: 机器数据

        Returns:
            bool: 是否添加成功
        """
        print("添加机器功能暂未实现，请直接更新数据库文件")
        return False

    def update_machine(self, machine_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新机器信息

        注意：此方法暂未实现本地数据库版本，主要功能已迁移到本地数据库查询

        Args:
            machine_id: 机器ID
            update_data: 要更新的数据

        Returns:
            bool: 是否更新成功
        """
        print("更新机器功能暂未实现，请直接更新数据库文件")
        return False

    def delete_machine(self, machine_id: str) -> bool:
        """
        删除机器

        注意：此方法暂未实现本地数据库版本，主要功能已迁移到本地数据库查询

        Args:
            machine_id: 机器ID

        Returns:
            bool: 是否删除成功
        """
        print("删除机器功能暂未实现，请直接更新数据库文件")
        return False

# 全局机器管理器实例
machine_manager = MachineManager()