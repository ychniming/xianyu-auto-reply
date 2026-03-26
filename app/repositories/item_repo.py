"""商品信息仓储模块

提供商品数据的操作
"""
import json
from typing import List, Dict, Optional, Any
from loguru import logger


class ItemRepository:
    """商品数据访问层"""

    def __init__(self, db_manager):
        """初始化仓储

        Args:
            db_manager: DBManager实例引用
        """
        self._db = db_manager
        self.conn = db_manager.conn
        self.lock = db_manager.lock

    def save_item_basic_info(self, cookie_id: str, item_id: str, item_title: str = None,
                            item_description: str = None, item_category: str = None,
                            item_price: str = None) -> bool:
        """保存商品基本信息

        Args:
            cookie_id: 账号ID
            item_id: 商品ID
            item_title: 商品标题
            item_description: 商品描述
            item_category: 商品类目
            item_price: 商品价格

        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO item_info
                (cookie_id, item_id, item_title, item_description, item_category, item_price)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (cookie_id, item_id, item_title, item_description, item_category, item_price))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"保存商品基本信息失败: {e}")
                self.conn.rollback()
                return False

    def save_item_info(self, cookie_id: str, item_id: str, item_data: Dict[str, Any] = None) -> bool:
        """保存商品完整信息

        Args:
            cookie_id: 账号ID
            item_id: 商品ID
            item_data: 商品完整信息字典，包含title, description, category, price, detail, is_multi_spec

        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()

                if item_data is None:
                    item_data = {}

                item_title = item_data.get('title')
                item_description = item_data.get('description')
                item_category = item_data.get('category')
                item_price = item_data.get('price')
                item_detail = item_data.get('detail')
                is_multi_spec = item_data.get('is_multi_spec', False)

                cursor.execute('''
                INSERT OR REPLACE INTO item_info
                (cookie_id, item_id, item_title, item_description, item_category,
                 item_price, item_detail, is_multi_spec, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (cookie_id, item_id, item_title, item_description, item_category,
                      item_price, json.dumps(item_detail) if item_detail else None, is_multi_spec))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"保存商品信息失败: {e}")
                self.conn.rollback()
                return False

    def get_item_info(self, cookie_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """获取商品信息

        Args:
            cookie_id: 账号ID
            item_id: 商品ID

        Returns:
            Optional[Dict[str, Any]]: 商品信息字典，包含item_detail_parsed字段
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT * FROM item_info
                WHERE cookie_id = ? AND item_id = ?
                ''', (cookie_id, item_id))

                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    item_info = dict(zip(columns, row))

                    if item_info.get('item_detail'):
                        try:
                            item_info['item_detail_parsed'] = json.loads(item_info['item_detail'])
                        except (json.JSONDecodeError, TypeError):
                            item_info['item_detail_parsed'] = {}

                    return item_info
                return None
            except Exception as e:
                logger.error(f"获取商品信息失败: {e}")
                return None

    def update_item_multi_spec_status(self, cookie_id: str, item_id: str, is_multi_spec: bool) -> bool:
        """更新商品多规格状态

        Args:
            cookie_id: 账号ID
            item_id: 商品ID
            is_multi_spec: 是否为多规格商品

        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                UPDATE item_info SET is_multi_spec = ?, updated_at = CURRENT_TIMESTAMP
                WHERE cookie_id = ? AND item_id = ?
                ''', (is_multi_spec, cookie_id, item_id))
                self.conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"更新商品多规格状态失败: {e}")
                return False

    def get_item_multi_spec_status(self, cookie_id: str, item_id: str) -> bool:
        """获取商品的多规格状态

        Args:
            cookie_id: 账号ID
            item_id: 商品ID

        Returns:
            bool: 是否为多规格商品
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT is_multi_spec FROM item_info
                WHERE cookie_id = ? AND item_id = ?
                ''', (cookie_id, item_id))

                row = cursor.fetchone()
                if row:
                    return bool(row[0]) if row[0] is not None else False
                return False
            except Exception as e:
                logger.error(f"获取商品多规格状态失败: {e}")
                return False

    def get_items_by_cookie_ids(self, cookie_ids: List[str]) -> List[Dict[str, Any]]:
        """批量获取多个账号的商品信息

        Args:
            cookie_ids: 账号ID列表

        Returns:
            List[Dict[str, Any]]: 所有账号的商品信息列表
        """
        if not cookie_ids:
            return []

        with self.lock:
            try:
                import time
                start_time = time.time()

                cursor = self.conn.cursor()
                placeholders = ','.join(['?' for _ in cookie_ids])
                cursor.execute(f'''
                SELECT * FROM item_info
                WHERE cookie_id IN ({placeholders})
                ORDER BY updated_at DESC
                ''', cookie_ids)

                query_time = time.time() - start_time
                logger.info(f"批量查询商品耗时: {query_time:.3f}秒, 查询账号数: {len(cookie_ids)}")

                columns = [description[0] for description in cursor.description]
                items = []

                for row in cursor.fetchall():
                    item_info = dict(zip(columns, row))

                    if item_info.get('item_detail'):
                        try:
                            item_info['item_detail_parsed'] = json.loads(item_info['item_detail'])
                        except (json.JSONDecodeError, TypeError):
                            item_info['item_detail_parsed'] = {}

                    items.append(item_info)

                logger.info(f"批量查询返回商品数: {len(items)}")
                return items
            except Exception as e:
                logger.error(f"批量获取商品信息失败: {e}")
                return []

    def get_items_by_cookie(self, cookie_id: str) -> List[Dict[str, Any]]:
        """获取指定Cookie的所有商品信息

        Args:
            cookie_id: 账号ID

        Returns:
            List[Dict[str, Any]]: 商品信息列表
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT * FROM item_info
                WHERE cookie_id = ?
                ORDER BY updated_at DESC
                ''', (cookie_id,))

                columns = [description[0] for description in cursor.description]
                items = []

                for row in cursor.fetchall():
                    item_info = dict(zip(columns, row))

                    if item_info.get('item_detail'):
                        try:
                            item_info['item_detail_parsed'] = json.loads(item_info['item_detail'])
                        except (json.JSONDecodeError, TypeError):
                            item_info['item_detail_parsed'] = {}

                    items.append(item_info)

                return items
            except Exception as e:
                logger.error(f"获取Cookie商品信息失败: {e}")
                return []

    def get_all_items(self) -> List[Dict[str, Any]]:
        """获取所有商品信息

        Returns:
            List[Dict[str, Any]]: 所有商品信息列表
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT * FROM item_info
                ORDER BY updated_at DESC
                ''')

                columns = [description[0] for description in cursor.description]
                items = []

                for row in cursor.fetchall():
                    item_info = dict(zip(columns, row))

                    if item_info.get('item_detail'):
                        try:
                            item_info['item_detail_parsed'] = json.loads(item_info['item_detail'])
                        except (json.JSONDecodeError, TypeError):
                            item_info['item_detail_parsed'] = {}

                    items.append(item_info)

                return items
            except Exception as e:
                logger.error(f"获取所有商品信息失败: {e}")
                return []

    def update_item_detail(self, cookie_id: str, item_id: str, item_detail: str) -> bool:
        """更新商品详情

        Args:
            cookie_id: 账号ID
            item_id: 商品ID
            item_detail: 商品详情（JSON字符串）

        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                UPDATE item_info SET item_detail = ?, updated_at = CURRENT_TIMESTAMP
                WHERE cookie_id = ? AND item_id = ?
                ''', (item_detail, cookie_id, item_id))
                self.conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"更新商品详情失败: {e}")
                return False
