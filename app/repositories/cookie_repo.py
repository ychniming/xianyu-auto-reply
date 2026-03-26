"""Cookie仓储模块

提供Cookie数据的增删改查操作
"""
from typing import Dict, Optional, Any
from loguru import logger


class CookieRepository:
    """Cookie数据访问层"""

    def __init__(self, db_manager):
        """初始化仓储

        Args:
            db_manager: DBManager实例引用
        """
        self._db = db_manager
        self.conn = db_manager.conn
        self.lock = db_manager.lock

    def save_cookie(self, cookie_id: str, cookie_value: str, user_id: int = None) -> bool:
        """保存Cookie到数据库，如存在则更新"""
        with self.lock:
            try:
                cursor = self.conn.cursor()

                if user_id is None:
                    self._db._execute_sql(cursor, "SELECT user_id FROM cookies WHERE id = ?", (cookie_id,))
                    existing = cursor.fetchone()
                    if existing:
                        user_id = existing[0]
                    else:
                        self._db._execute_sql(cursor, "SELECT id FROM users WHERE username = 'admin'")
                        admin_user = cursor.fetchone()
                        user_id = admin_user[0] if admin_user else 1

                self._db._execute_sql(cursor,
                    "INSERT OR REPLACE INTO cookies (id, value, user_id) VALUES (?, ?, ?)",
                    (cookie_id, cookie_value, user_id)
                )

                cursor.execute('''
                INSERT OR REPLACE INTO cookie_status (cookie_id, enabled, updated_at)
                VALUES (?, 1, CURRENT_TIMESTAMP)
                ''', (cookie_id,))

                self.conn.commit()
                logger.info(f"Cookie保存成功: {cookie_id} (用户ID: {user_id})")

                self._db._execute_sql(cursor, "SELECT user_id FROM cookies WHERE id = ?", (cookie_id,))
                saved_user_id = cursor.fetchone()
                if saved_user_id:
                    logger.info(f"Cookie保存验证: {cookie_id} 实际绑定到用户ID: {saved_user_id[0]}")
                else:
                    logger.error(f"Cookie保存验证失败: {cookie_id} 未找到记录")
                return True
            except Exception as e:
                logger.error(f"Cookie保存失败: {e}")
                self.conn.rollback()
                return False

    def delete_cookie(self, cookie_id: str) -> bool:
        """从数据库删除Cookie及其关键字"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "DELETE FROM keywords WHERE cookie_id = ?", (cookie_id,))
                self._db._execute_sql(cursor, "DELETE FROM cookie_status WHERE cookie_id = ?", (cookie_id,))
                self._db._execute_sql(cursor, "DELETE FROM cookies WHERE id = ?", (cookie_id,))
                self.conn.commit()
                logger.debug(f"Cookie删除成功: {cookie_id}")
                return True
            except Exception as e:
                logger.error(f"Cookie删除失败: {e}")
                self.conn.rollback()
                return False

    def get_cookie(self, cookie_id: str) -> Optional[str]:
        """获取指定Cookie值"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "SELECT value FROM cookies WHERE id = ?", (cookie_id,))
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                logger.error(f"获取Cookie失败: {e}")
                return None

    def get_all_cookies(self, user_id: int = None) -> Dict[str, str]:
        """获取所有Cookie（支持用户隔离）"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if user_id is not None:
                    self._db._execute_sql(cursor, "SELECT id, value FROM cookies WHERE user_id = ?", (user_id,))
                else:
                    self._db._execute_sql(cursor, "SELECT id, value FROM cookies")
                return {row[0]: row[1] for row in cursor.fetchall()}
            except Exception as e:
                logger.error(f"获取所有Cookie失败: {e}")
                return {}

    def get_cookie_by_id(self, cookie_id: str) -> Optional[Dict[str, str]]:
        """根据ID获取Cookie信息"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "SELECT id, value, created_at FROM cookies WHERE id = ?", (cookie_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'cookies_str': result[1],
                        'value': result[1],
                        'created_at': result[2]
                    }
                return None
            except Exception as e:
                logger.error(f"根据ID获取Cookie失败: {e}")
                return None

    def get_cookie_details(self, cookie_id: str) -> Optional[Dict[str, Any]]:
        """获取Cookie的详细信息，包括user_id和auto_confirm"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor,
                    "SELECT id, value, user_id, auto_confirm, created_at FROM cookies WHERE id = ?",
                    (cookie_id,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'value': result[1],
                        'user_id': result[2],
                        'auto_confirm': bool(result[3]),
                        'created_at': result[4]
                    }
                return None
            except Exception as e:
                logger.error(f"获取Cookie详细信息失败: {e}")
                return None

    def update_auto_confirm(self, cookie_id: str, auto_confirm: bool) -> bool:
        """更新Cookie的自动确认发货设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor,
                    "UPDATE cookies SET auto_confirm = ? WHERE id = ?",
                    (int(auto_confirm), cookie_id)
                )
                self.conn.commit()
                logger.info(f"更新账号 {cookie_id} 自动确认发货设置: {'开启' if auto_confirm else '关闭'}")
                return True
            except Exception as e:
                logger.error(f"更新自动确认发货设置失败: {e}")
                return False

    def get_auto_confirm(self, cookie_id: str) -> bool:
        """获取Cookie的自动确认发货设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "SELECT auto_confirm FROM cookies WHERE id = ?", (cookie_id,))
                result = cursor.fetchone()
                if result:
                    return bool(result[0])
                return True
            except Exception as e:
                logger.error(f"获取自动确认发货设置失败: {e}")
                return True

    def save_cookie_status(self, cookie_id: str, enabled: bool) -> None:
        """保存Cookie的启用状态"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO cookie_status (cookie_id, enabled, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (cookie_id, enabled))
                self.conn.commit()
                logger.debug(f"保存Cookie状态: {cookie_id} -> {'启用' if enabled else '禁用'}")
            except Exception as e:
                logger.error(f"保存Cookie状态失败: {e}")
                raise

    def get_cookie_status(self, cookie_id: str) -> bool:
        """获取Cookie的启用状态"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT enabled FROM cookie_status WHERE cookie_id = ?', (cookie_id,))
                result = cursor.fetchone()
                return bool(result[0]) if result else True
            except Exception as e:
                logger.error(f"获取Cookie状态失败: {e}")
                return True

    def get_all_cookie_status(self) -> Dict[str, bool]:
        """获取所有Cookie的启用状态"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT cookie_id, enabled FROM cookie_status')
                result = {}
                for row in cursor.fetchall():
                    cookie_id, enabled = row
                    result[cookie_id] = bool(enabled)
                return result
            except Exception as e:
                logger.error(f"获取所有Cookie状态失败: {e}")
                return {}
