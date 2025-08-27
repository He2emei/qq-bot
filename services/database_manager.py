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

            # 创建机器表 - 移除name的UNIQUE约束，添加复合约束
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS machines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    region TEXT,
                    dimension TEXT,
                    coordinates TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, region, coordinates)
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

            # 创建FAQ表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS faq (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    contents TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

                            # 插入机器 - 使用INSERT OR IGNORE来避免覆盖重复记录
                            cursor.execute('''
                                INSERT OR IGNORE INTO machines (name, region, dimension, coordinates)
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
                            m.created_at, m.updated_at,
                            GROUP_CONCAT(p.name, ', ') as products,
                            GROUP_CONCAT(mt.name, ', ') as maintainers
                    FROM machines m
                    LEFT JOIN machine_products mp ON m.id = mp.machine_id
                    LEFT JOIN products p ON mp.product_id = p.id
                    LEFT JOIN machine_maintainers mm ON m.id = mm.machine_id
                    LEFT JOIN maintainers mt ON mm.maintainer_id = mt.id
                    WHERE m.name = ?
                    GROUP BY m.id, m.name, m.region, m.dimension, m.coordinates, m.created_at, m.updated_at
                '''

                cursor.execute(query, (machine_name,))
                row = cursor.fetchone()

                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'region': row[2] or '',
                        'dimension': row[3] or '',
                        'coordinates': row[4] or '',
                        'created_time': row[5] or '',
                        'last_edited_time': row[6] or '',
                        'products': row[7].split(', ') if row[7] else [],
                        'maintainers': row[8].split(', ') if row[8] else []
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

    def get_faq_content(self, key: str) -> Optional[str]:
        """根据key获取FAQ内容"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT contents FROM faq WHERE key = ?', (key,))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"获取FAQ内容失败: {e}")
            return None

    def set_faq_content(self, key: str, contents: str) -> bool:
        """设置或更新FAQ内容"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO faq (key, contents, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, contents))
                conn.commit()
                return True
        except Exception as e:
            print(f"设置FAQ内容失败: {e}")
            return False

    def delete_faq_content(self, key: str) -> bool:
        """删除FAQ条目"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM faq WHERE key = ?', (key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除FAQ内容失败: {e}")
            return False

    def list_all_faq_keys(self) -> List[str]:
        """获取所有FAQ key列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key FROM faq ORDER BY key')
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            print(f"获取FAQ列表失败: {e}")
            return []

    def add_machine(self, machine_data: Dict[str, Any]) -> Optional[int]:
        """添加新机器到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 插入机器基本信息
                cursor.execute('''
                    INSERT INTO machines (name, region, dimension, coordinates)
                    VALUES (?, ?, ?, ?)
                ''', (
                    machine_data['name'],
                    machine_data.get('region'),
                    machine_data.get('dimension'),
                    machine_data.get('coordinates')
                ))

                machine_id = cursor.lastrowid

                # 处理产物
                if machine_data.get('products'):
                    products = machine_data['products'] if isinstance(machine_data['products'], list) else [machine_data['products']]
                    for product_name in products:
                        if product_name.strip():
                            # 插入或获取产物ID
                            cursor.execute('INSERT OR IGNORE INTO products (name) VALUES (?)', (product_name.strip(),))
                            cursor.execute('SELECT id FROM products WHERE name = ?', (product_name.strip(),))
                            product_id = cursor.fetchone()[0]

                            # 关联机器和产物
                            cursor.execute('INSERT OR IGNORE INTO machine_products (machine_id, product_id) VALUES (?, ?)',
                                         (machine_id, product_id))

                # 处理维护者
                if machine_data.get('maintainers'):
                    maintainers = machine_data['maintainers'] if isinstance(machine_data['maintainers'], list) else [machine_data['maintainers']]
                    for maintainer_name in maintainers:
                        if maintainer_name.strip():
                            # 插入或获取维护者ID
                            cursor.execute('INSERT OR IGNORE INTO maintainers (name) VALUES (?)', (maintainer_name.strip(),))
                            cursor.execute('SELECT id FROM maintainers WHERE name = ?', (maintainer_name.strip(),))
                            maintainer_id = cursor.fetchone()[0]

                            # 关联机器和维护者
                            cursor.execute('INSERT OR IGNORE INTO machine_maintainers (machine_id, maintainer_id) VALUES (?, ?)',
                                         (machine_id, maintainer_id))

                # 处理地域
                if machine_data.get('region'):
                    cursor.execute('INSERT OR IGNORE INTO regions (name) VALUES (?)', (machine_data['region'],))

                conn.commit()
                return machine_id

        except Exception as e:
            print(f"添加机器失败: {e}")
            return None

    def update_machine(self, machine_id: int, update_data: Dict[str, Any]) -> bool:
        """更新机器信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 更新机器基本信息
                if any(key in update_data for key in ['name', 'region', 'dimension', 'coordinates']):
                    update_fields = []
                    values = []

                    if 'name' in update_data:
                        update_fields.append('name = ?')
                        values.append(update_data['name'])

                    if 'region' in update_data:
                        update_fields.append('region = ?')
                        values.append(update_data['region'])
                        # 确保地域存在
                        cursor.execute('INSERT OR IGNORE INTO regions (name) VALUES (?)', (update_data['region'],))

                    if 'dimension' in update_data:
                        update_fields.append('dimension = ?')
                        values.append(update_data['dimension'])

                    if 'coordinates' in update_data:
                        update_fields.append('coordinates = ?')
                        values.append(update_data['coordinates'])

                    update_fields.append('updated_at = CURRENT_TIMESTAMP')
                    values.append(machine_id)

                    query = f'UPDATE machines SET {", ".join(update_fields)} WHERE id = ?'
                    cursor.execute(query, values)

                # 更新产物
                if 'products' in update_data:
                    # 删除现有的产物关联
                    cursor.execute('DELETE FROM machine_products WHERE machine_id = ?', (machine_id,))

                    # 添加新的产物关联
                    products = update_data['products'] if isinstance(update_data['products'], list) else [update_data['products']]
                    for product_name in products:
                        if product_name.strip():
                            cursor.execute('INSERT OR IGNORE INTO products (name) VALUES (?)', (product_name.strip(),))
                            cursor.execute('SELECT id FROM products WHERE name = ?', (product_name.strip(),))
                            product_id = cursor.fetchone()[0]
                            cursor.execute('INSERT OR IGNORE INTO machine_products (machine_id, product_id) VALUES (?, ?)',
                                         (machine_id, product_id))

                # 更新维护者
                if 'maintainers' in update_data:
                    # 删除现有的维护者关联
                    cursor.execute('DELETE FROM machine_maintainers WHERE machine_id = ?', (machine_id,))

                    # 添加新的维护者关联
                    maintainers = update_data['maintainers'] if isinstance(update_data['maintainers'], list) else [update_data['maintainers']]
                    for maintainer_name in maintainers:
                        if maintainer_name.strip():
                            cursor.execute('INSERT OR IGNORE INTO maintainers (name) VALUES (?)', (maintainer_name.strip(),))
                            cursor.execute('SELECT id FROM maintainers WHERE name = ?', (maintainer_name.strip(),))
                            maintainer_id = cursor.fetchone()[0]
                            cursor.execute('INSERT OR IGNORE INTO machine_maintainers (machine_id, maintainer_id) VALUES (?, ?)',
                                         (machine_id, maintainer_id))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"更新机器失败: {e}")
            return False

    def delete_machine(self, machine_id: int) -> bool:
        """删除机器"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 删除机器（级联删除会自动删除关联表中的记录）
                cursor.execute('DELETE FROM machines WHERE id = ?', (machine_id,))
                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"删除机器失败: {e}")
            return False

    def get_machine_id_by_name(self, machine_name: str) -> Optional[int]:
        """根据机器名称获取ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM machines WHERE name = ?', (machine_name,))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"获取机器ID失败: {e}")
            return None

# 全局数据库管理器实例
database_manager = DatabaseManager()