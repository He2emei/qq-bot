# services/machine_manager.py
import json
from typing import Dict, Any, List, Optional
from services.notion_service import NotionService
import config

class MachineManager:
    """
    机器数据库管理器

    负责管理Notion中的机器数据库，包括：
    - 根据产物查询机器
    - 添加/编辑机器信息
    - 查询机器详细信息
    """

    def __init__(self):
        self.notion_service = NotionService()

    def search_machines_by_product(self, product: str) -> List[Dict[str, Any]]:
        """
        根据产物搜索机器

        Args:
            product: 产物名称

        Returns:
            List[Dict[str, Any]]: 匹配的机器列表
        """
        try:
            # 首先在产物数据库中查找对应的产物页面
            product_page = self._find_product_by_name(product)
            if not product_page:
                print(f"未找到产物: {product}")
                return []

            # 通过relation查询与该产物关联的机器
            return self._search_machines_by_relation("产物", product_page['id'])

        except Exception as e:
            print(f"查询机器失败: {e}")
            return []

    def _find_product_by_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """
        根据产物名称查找产物页面

        Args:
            product_name: 产物名称

        Returns:
            Optional[Dict[str, Any]]: 产物页面信息
        """
        try:
            database_id = config.NOTION_DATABASES['products']
            url = f"{self.notion_service.base_url}databases/{database_id}/query/"

            payload = {
                "filter": {
                    "property": "Name",
                    "title": {
                        "equals": product_name
                    }
                }
            }

            response = self.notion_service.session.post(
                url,
                headers=self.notion_service.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if result.get('results'):
                return result['results'][0]
            return None

        except Exception as e:
            print(f"查找产物失败: {e}")
            return None

    def _search_machines_by_relation(self, relation_property: str, related_page_id: str) -> List[Dict[str, Any]]:
        """
        通过relation属性搜索机器

        Args:
            relation_property: relation属性名称
            related_page_id: 关联的页面ID

        Returns:
            List[Dict[str, Any]]: 匹配的机器列表
        """
        try:
            database_id = config.NOTION_DATABASES['machines']
            url = f"{self.notion_service.base_url}databases/{database_id}/query/"

            payload = {
                "filter": {
                    "property": relation_property,
                    "relation": {
                        "contains": related_page_id
                    }
                }
            }

            response = self.notion_service.session.post(
                url,
                headers=self.notion_service.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            machines = []
            for page in result.get('results', []):
                machine_info = self._parse_machine_page(page)
                if machine_info:
                    machines.append(machine_info)

            return machines

        except Exception as e:
            print(f"通过relation查询机器失败: {e}")
            return []

    def _get_page_name_by_id(self, page_id: str) -> Optional[str]:
        """
        根据页面ID获取页面名称

        Args:
            page_id: 页面ID

        Returns:
            Optional[str]: 页面名称
        """
        try:
            url = f"{self.notion_service.base_url}pages/{page_id}"

            response = self.notion_service.session.get(
                url,
                headers=self.notion_service.headers
            )
            response.raise_for_status()
            page_data = response.json()

            # 获取页面标题
            properties = page_data.get('properties', {})
            if properties.get('Name', {}).get('title'):
                title_items = properties['Name']['title']
                if title_items:
                    return title_items[0].get('plain_text', '')

            return None

        except Exception as e:
            print(f"获取页面名称失败: {e}")
            return None

    def search_machines_by_region(self, region: str) -> List[Dict[str, Any]]:
        """
        根据地域搜索机器

        Args:
            region: 地域名称

        Returns:
            List[Dict[str, Any]]: 匹配的机器列表
        """
        try:
            # 首先在地域数据库中查找对应的地域页面
            region_page = self._find_region_by_name(region)
            if not region_page:
                print(f"未找到地域: {region}")
                return []

            # 通过relation查询与该地域关联的机器
            return self._search_machines_by_relation("地域", region_page['id'])

        except Exception as e:
            print(f"查询地域机器失败: {e}")
            return []

    def _find_region_by_name(self, region_name: str) -> Optional[Dict[str, Any]]:
        """
        根据地域名称查找地域页面

        Args:
            region_name: 地域名称

        Returns:
            Optional[Dict[str, Any]]: 地域页面信息
        """
        try:
            database_id = config.NOTION_DATABASES['regions']
            url = f"{self.notion_service.base_url}databases/{database_id}/query/"

            payload = {
                "filter": {
                    "property": "Name",
                    "title": {
                        "equals": region_name
                    }
                }
            }

            response = self.notion_service.session.post(
                url,
                headers=self.notion_service.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if result.get('results'):
                return result['results'][0]
            return None

        except Exception as e:
            print(f"查找地域失败: {e}")
            return None

    def get_machine_details(self, machine_name: str) -> Optional[Dict[str, Any]]:
        """
        获取机器详细信息

        Args:
            machine_name: 机器名称

        Returns:
            Optional[Dict[str, Any]]: 机器详细信息
        """
        try:
            database_id = config.NOTION_DATABASES['machines']
            url = f"{self.notion_service.base_url}databases/{database_id}/query/"

            payload = {
                "filter": {
                    "property": "Name",
                    "title": {
                        "equals": machine_name
                    }
                }
            }

            response = self.notion_service.session.post(
                url,
                headers=self.notion_service.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if result.get('results'):
                return self._parse_machine_page(result['results'][0])

            return None

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
            database_id = config.NOTION_DATABASES['regions']
            url = f"{self.notion_service.base_url}databases/{database_id}/query/"

            # 获取所有地域页面
            response = self.notion_service.session.post(
                url,
                headers=self.notion_service.headers,
                json={}
            )
            response.raise_for_status()
            result = response.json()

            regions = []
            for page in result.get('results', []):
                properties = page.get('properties', {})
                if properties.get('Name', {}).get('title'):
                    title_items = properties['Name']['title']
                    if title_items:
                        region_name = title_items[0].get('plain_text', '')
                        if region_name:
                            regions.append(region_name)

            return sorted(regions)

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
            database_id = config.NOTION_DATABASES['products']
            url = f"{self.notion_service.base_url}databases/{database_id}/query/"

            response = self.notion_service.session.post(
                url,
                headers=self.notion_service.headers,
                json={}
            )
            response.raise_for_status()
            result = response.json()

            products = []
            for page in result.get('results', []):
                properties = page.get('properties', {})
                if properties.get('Name', {}).get('title'):
                    title_items = properties['Name']['title']
                    if title_items:
                        product_name = title_items[0].get('plain_text', '')
                        if product_name:
                            products.append(product_name)

            return sorted(products)

        except Exception as e:
            print(f"获取产物列表失败: {e}")
            return []

    def _parse_machine_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析Notion页面数据为机器信息

        Args:
            page: Notion页面数据

        Returns:
            Dict[str, Any]: 解析后的机器信息
        """
        try:
            properties = page.get('properties', {})

            # 解析基本信息 - 使用实际的属性名称
            name = ""
            if properties.get('Name', {}).get('title'):  # 名称
                title_items = properties['Name']['title']
                if title_items:
                    name = title_items[0].get('plain_text', '')

            # 解析地域 - 处理relation属性
            region = ""
            if properties.get('地域', {}).get('relation'):
                relations = properties['地域']['relation']
                if relations:
                    # 获取第一个关联的地域页面的名称
                    region_page = self._get_page_name_by_id(relations[0]['id'])
                    if region_page:
                        region = region_page

            # 解析产物 - 处理relation属性
            products = []
            if properties.get('产物', {}).get('relation'):
                relations = properties['产物']['relation']
                for relation in relations:
                    product_page = self._get_page_name_by_id(relation['id'])
                    if product_page:
                        products.append(product_page)

            # 解析可维护者
            maintainers = []
            if properties.get('可维护者', {}).get('people'):
                for person in properties['可维护者']['people']:
                    person_name = person.get('name', '')
                    if person_name:
                        maintainers.append(person_name)

            # 解析维度和坐标
            dimension = ""
            coordinates = ""
            if properties.get('维度', {}).get('rich_text'):
                for item in properties['维度']['rich_text']:
                    dimension += item.get('plain_text', '')
            if properties.get('坐标', {}).get('rich_text'):
                for item in properties['坐标']['rich_text']:
                    coordinates += item.get('plain_text', '')

            return {
                'id': page.get('id', ''),
                'name': name,
                'region': region,
                'products': products,
                'maintainers': maintainers,
                'dimension': dimension,
                'coordinates': coordinates,
                'created_time': page.get('created_time', ''),
                'last_edited_time': page.get('last_edited_time', '')
            }

        except Exception as e:
            print(f"解析机器页面失败: {e}")
            return {}

    def add_machine(self, machine_data: Dict[str, Any]) -> bool:
        """
        添加新机器到数据库

        Args:
            machine_data: 机器数据，包含：
                - name: 机器名称
                - region: 地域
                - products: 产物列表
                - maintainers: 维护者列表
                - dimension: 维度
                - coordinates: 坐标

        Returns:
            bool: 是否添加成功
        """
        try:
            database_id = config.NOTION_DATABASES['machines']
            url = f"{self.notion_service.base_url}pages/"

            # 构建页面数据
            page_data = {
                "parent": {
                    "type": "database_id",
                    "database_id": database_id
                },
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": machine_data.get('name', '')
                                }
                            }
                        ]
                    },
                    "地域": {
                        "select": {
                            "name": machine_data.get('region', '')
                        }
                    },
                    "产物": {
                        "multi_select": [
                            {"name": product}
                            for product in machine_data.get('products', [])
                        ]
                    },
                    "可维护者": {
                        "people": []  # Notion API中添加people需要复杂的逻辑，这里先留空
                    },
                    "维度": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": machine_data.get('dimension', '')
                                }
                            }
                        ]
                    },
                    "坐标": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": machine_data.get('coordinates', '')
                                }
                            }
                        ]
                    }
                }
            }

            response = self.notion_service.session.post(
                url,
                headers=self.notion_service.headers,
                json=page_data
            )
            response.raise_for_status()

            print(f"成功添加机器: {machine_data.get('name', '')}")
            return True

        except Exception as e:
            print(f"添加机器失败: {e}")
            return False

    def update_machine(self, machine_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新机器信息

        Args:
            machine_id: 机器页面ID
            update_data: 要更新的数据

        Returns:
            bool: 是否更新成功
        """
        try:
            url = f"{self.notion_service.base_url}pages/{machine_id}"

            # 构建更新数据
            properties = {}

            if 'name' in update_data:
                properties['Name'] = {
                    "title": [
                        {
                            "text": {
                                "content": update_data['name']
                            }
                        }
                    ]
                }

            if 'region' in update_data:
                properties['地域'] = {
                    "select": {
                        "name": update_data['region']
                    }
                }

            if 'products' in update_data:
                properties['产物'] = {
                    "multi_select": [
                        {"name": product}
                        for product in update_data['products']
                    ]
                }

            if 'dimension' in update_data:
                properties['维度'] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": update_data['dimension']
                            }
                        }
                    ]
                }

            if 'coordinates' in update_data:
                properties['坐标'] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": update_data['coordinates']
                            }
                        }
                    ]
                }

            payload = {"properties": properties}

            response = self.notion_service.session.patch(
                url,
                headers=self.notion_service.headers,
                json=payload
            )
            response.raise_for_status()

            print(f"成功更新机器: {machine_id}")
            return True

        except Exception as e:
            print(f"更新机器失败: {e}")
            return False

    def delete_machine(self, machine_id: str) -> bool:
        """
        删除机器（通过添加删除标记实现）

        Args:
            machine_id: 机器页面ID

        Returns:
            bool: 是否删除成功
        """
        try:
            url = f"{self.notion_service.base_url}pages/{machine_id}"

            payload = {
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": f"[已删除] {self.get_machine_details(machine_id.split('-')[0])['name'] if machine_id else '未知'}"
                                }
                            }
                        ]
                    }
                },
                "archived": True
            }

            response = self.notion_service.session.patch(
                url,
                headers=self.notion_service.headers,
                json=payload
            )
            response.raise_for_status()

            print(f"成功删除机器: {machine_id}")
            return True

        except Exception as e:
            print(f"删除机器失败: {e}")
            return False

# 全局机器管理器实例
machine_manager = MachineManager()