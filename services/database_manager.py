# services/database_manager.py
import sqlite3
import os
from typing import List, Dict, Any, Optional
import csv

class DatabaseManager:
    """本地数据库管理器"""

    def __init__(self, db_path: str = "data/machines.db"):
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()

    def _init_database(self):
        """初始化数据库和表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建机器表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS machines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    region TEXT,
                    dimension TEXT,
                    coordinates TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建产物表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建机器产物关联表（多对多关系）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS machine_products (
                    machine_id INTEGER,
                    product_id INTEGER,
                    FOREIGN KEY (machine_id) REFERENCES machines (id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
                    PRIMARY KEY (machine_id, product_id)
                )
            ''')

            # 创建维护者表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintainers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建机器维护者关联表（多对多关系）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS machine_maintainers (
                    machine_id INTEGER,
                    maintainer_id INTEGER,
                    FOREIGN KEY (machine_id) REFERENCES machines (id) ON DELETE CASCADE,
                    FOREIGN KEY (maintainer_id) REFERENCES maintainers (id) ON DELETE CASCADE,
                    PRIMARY KEY (machine_id, maintainer_id)
                )
            ''')

            # 创建地域表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS regions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def import_from_csv(self, csv_path: str) -> bool:
        """从CSV文件导入数据"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # 跳过表头

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    for row in reader:
                        if len(row) >= 6:
                            name = row[0].strip()
                            region_full = row[1].strip()
                            products_full = row[2].strip()
                            maintainer = row[3].strip()
                            dimension = row[4].strip()
                            coordinates = row[5].strip()

                            # 提取地域名称（去除链接部分）
                            region_name = ""
                            if region_full:
                                # 提取括号前的地域名称
                                if " (" in region_full:
                                    region_name = region_full.split(" (")[0]
                                else:
                                    region_name = region_full

                            # 处理产物（可能包含多个，用逗号分隔）
                            product_list = []
                            if products_full:
                                # 移除链接部分，提取产物名称
                                products_clean = products_full
                                # 处理多个产物的情况
                                for product in products_clean.split(','):
                                    product = product.strip()
                                    if product and " (" in product:
                                        product_name = product.split(" (")[0]
                                        product_list.append(product_name)
                                    elif product:
                                        product_list.append(product)

                            # 插入或获取地域ID
                            region_id = None
                            if region_name:
                                cursor.execute('INSERT OR IGNORE INTO regions (name) VALUES (?)', (region_name,))
                                cursor.execute('SELECT id FROM regions WHERE name = ?', (region_name,))
                                region_id = cursor.fetchone()[0]

                            # 插入机器
                            cursor.execute('''
                                INSERT OR REPLACE INTO machines (name, region, dimension, coordinates)
                                VALUES (?, ?, ?, ?)
                            ''', (name, region_name, dimension, coordinates))

                            machine_id = cursor.lastrowid

                            # 处理产物
                            for product_name in product_list:
                                if product_name:
                                    # 插入或获取产物ID
                                    cursor.execute('INSERT OR IGNORE INTO products (name) VALUES (?)', (product_name,))
                                    cursor.execute('SELECT id FROM products WHERE name = ?', (product_name,))
                                    product_id = cursor.fetchone()[0]

                                    # 关联机器和产物
                                    cursor.execute('INSERT OR IGNORE INTO machine_products (machine_id, product_id) VALUES (?, ?)',
                                                 (machine_id, product_id))

                            # 处理维护者
                            if maintainer:
                                cursor.execute('INSERT OR IGNORE INTO maintainers (name) VALUES (?)', (maintainer,))
                                cursor.execute('SELECT id FROM maintainers WHERE name = ?', (maintainer,))
                                maintainer_id = cursor.fetchone()[0]

                                # 关联机器和维护者
                                cursor.execute('INSERT OR IGNORE INTO machine_maintainers (machine_id, maintainer_id) VALUES (?, ?)',
                                             (machine_id, maintainer_id))

                    conn.commit()
                    print(f"成功从 {csv_path} 导入数据")
                    return True

        except Exception as e:
            print(f"导入CSV失败: {e}")
            return False

    def search_machines_by_product(self, product: str) -> List[Dict[str, Any]]:
        """根据产物搜索机器"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = '''
                    SELECT DISTINCT m.id, m.name, m.region, m.dimension, m.coordinates,
                           GROUP_CONCAT(p.name, ', ') as products,
                           GROUP_CONCAT(mt.name, ', ') as maintainers
                    FROM machines m
                    LEFT JOIN machine_products mp ON m.id = mp.machine_id
                    LEFT JOIN products p ON mp.product_id = p.id
                    LEFT JOIN machine_maintainers mm ON m.id = mm.machine_id
                    LEFT JOIN maintainers mt ON mm.maintainer_id = mt.id
                    WHERE m.id IN (
                        SELECT mp2.machine_id
                        FROM machine_products mp2
                        JOIN products p2 ON mp2.product_id = p2.id
                        WHERE p2.name LIKE ?
                    )
                    GROUP BY m.id, m.name, m.region, m.dimension, m.coordinates
                '''

                cursor.execute(query, (f'%{product}%',))
                rows = cursor.fetchall()

                machines = []
                for row in rows:
                    machine = {
                        'id': row[0],
                        'name': row[1],
                        'region': row[2] or '',
                        'products': row[5].split(', ') if row[5] else [],
                        'maintainers': row[6].split(', ') if row[6] else [],
                        'dimension': row[3] or '',
                        'coordinates': row[4] or ''
                    }
                    machines.append(machine)

                return machines

        except Exception as e:
            print(f"搜索机器失败: {e}")
            return []

    def search_machines_by_region(self, region: str) -> List[Dict[str, Any]]:
        """根据地域搜索机器"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = '''
                    SELECT m.id, m.name, m.region, m.dimension, m.coordinates,
                           GROUP_CONCAT(p.name, ', ') as products,
                           GROUP_CONCAT(mt.name, ', ') as maintainers
                    FROM machines m
                    LEFT JOIN machine_products mp ON m.id = mp.machine_id
                    LEFT JOIN products p ON mp.product_id = p.id
                    LEFT JOIN machine_maintainers mm ON m.id = mm.machine_id
                    LEFT JOIN maintainers mt ON mm.maintainer_id = mt.id
                    WHERE m.region LIKE ?
                    GROUP BY m.id, m.name, m.region, m.dimension, m.coordinates
                '''

                cursor.execute(query, (f'%{region}%',))
                rows = cursor.fetchall()

                machines = []
                for row in rows:
                    machine = {
                        'id': row[0],
                        'name': row[1],
                        'region': row[2] or '',
                        'products': row[5].split(', ') if row[5] else [],
                        'maintainers': row[6].split(', ') if row[6] else [],
                        'dimension': row[3] or '',
                        'coordinates': row[4] or ''
                    }
                    machines.append(machine)

                return machines

        except Exception as e:
            print(f"按地域搜索机器失败: {e}")
            return []

    def get_machine_details(self, machine_name: str) -> Optional[Dict[str, Any]]:
        """获取机器详细信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = '''
                    SELECT m.id, m.name, m.region, m.dimension, m.coordinates,
                           GROUP_CONCAT(p.name, ', ') as products,
                           GROUP_CONCAT(mt.name, ', ') as maintainers
                    FROM machines m
                    LEFT JOIN machine_products mp ON m.id = mp.machine_id
                    LEFT JOIN products p ON mp.product_id = p.id
                    LEFT JOIN machine_maintainers mm ON m.id = mm.machine_id
                    LEFT JOIN maintainers mt ON mm.maintainer_id = mt.id
                    WHERE m.name = ?
                    GROUP BY m.id, m.name, m.region, m.dimension, m.coordinates
                '''

                cursor.execute(query, (machine_name,))
                row = cursor.fetchone()

                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'region': row[2] or '',
                        'products': row[5].split(', ') if row[5] else [],
                        'maintainers': row[6].split(', ') if row[6] else [],
                        'dimension': row[3] or '',
                        'coordinates': row[4] or ''
                    }

                return None

        except Exception as e:
            print(f"获取机器详情失败: {e}")
            return None

    def list_all_regions(self) -> List[str]:
        """获取所有地域列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM regions ORDER BY name')
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            print(f"获取地域列表失败: {e}")
            return []

    def list_all_products(self) -> List[str]:
        """获取所有产物列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM products ORDER BY name')
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            print(f"获取产物列表失败: {e}")
            return []

# 全局数据库管理器实例
database_manager = DatabaseManager()