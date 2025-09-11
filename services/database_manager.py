# services/database_manager.py
import sqlite3
import os
from typing import List, Optional

class DatabaseManager:
    """本地FAQ数据库管理器"""

    def __init__(self, db_path: str = "data/faq.db"):
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()

    def _init_database(self):
        """初始化数据库和表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

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

# 全局FAQ数据库管理器实例
database_manager = DatabaseManager()