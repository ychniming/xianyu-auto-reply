"""Cookie仓储模块

提供Cookie数据的增删改查操作
"""
from typing import Dict, Optional, Any
from loguru import logger

from app.utils.encryption import encrypt, decrypt, EncryptionError


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
        """保存Cookie到数据库，如存在则更新
        
        Args:
            cookie_id: Cookie ID
            cookie_value: Cookie值（明文）
            user_id: 用户ID
            
        Returns:
            bool: 保存是否成功
        """
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

                # 加密Cookie值
                encrypted_value = None
                if cookie_value:
                    try:
                        encrypted_value = encrypt(cookie_value)
                        logger.debug(f"Cookie加密成功: {cookie_id}")
                    except EncryptionError as e:
                        logger.error(f"Cookie加密失败: {cookie_id}, {e}")
                        return False

                # 保存到数据库，value字段置空，只存储加密后的值
                self._db._execute_sql(cursor,
                    "INSERT OR REPLACE INTO cookies (id, value, value_encrypted, user_id) VALUES (?, ?, ?, ?)",
                    (cookie_id, None, encrypted_value, user_id)
                )

                cursor.execute('''
                INSERT OR REPLACE INTO cookie_status (cookie_id, enabled, updated_at)
                VALUES (?, 1, CURRENT_TIMESTAMP)
                ''', (cookie_id,))

                self.conn.commit()
                logger.info(f"Cookie保存成功（已加密）: {cookie_id} (用户ID: {user_id})")

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
        """从数据库删除Cookie及其关联数据

        使用事务确保删除操作的原子性，同时删除：
        - Cookie记录
        - 关键词记录
        - Cookie状态记录
        - 默认回复设置
        - AI回复设置

        Args:
            cookie_id: Cookie ID

        Returns:
            bool: 删除是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # 删除关联的关键词
                self._db._execute_sql(cursor, "DELETE FROM keywords WHERE cookie_id = ?", (cookie_id,))
                logger.debug(f"删除关联关键词: {cookie_id}")

                # 删除Cookie状态
                self._db._execute_sql(cursor, "DELETE FROM cookie_status WHERE cookie_id = ?", (cookie_id,))
                logger.debug(f"删除Cookie状态: {cookie_id}")

                # 删除默认回复设置
                self._db._execute_sql(cursor, "DELETE FROM default_replies WHERE cookie_id = ?", (cookie_id,))
                logger.debug(f"删除默认回复设置: {cookie_id}")

                # 删除AI回复设置
                self._db._execute_sql(cursor, "DELETE FROM ai_reply_settings WHERE cookie_id = ?", (cookie_id,))
                logger.debug(f"删除AI回复设置: {cookie_id}")

                # 删除AI对话记录
                self._db._execute_sql(cursor, "DELETE FROM ai_conversations WHERE cookie_id = ?", (cookie_id,))
                logger.debug(f"删除AI对话记录: {cookie_id}")

                # 最后删除Cookie本身
                self._db._execute_sql(cursor, "DELETE FROM cookies WHERE id = ?", (cookie_id,))

                self.conn.commit()
                logger.info(f"Cookie删除成功: {cookie_id}")
                return True
            except Exception as e:
                logger.error(f"Cookie删除失败: {e}")
                self.conn.rollback()
                return False

    def get_cookie(self, cookie_id: str) -> Optional[str]:
        """获取指定Cookie值（解密后）
        
        Args:
            cookie_id: Cookie ID
            
        Returns:
            Optional[str]: 解密后的Cookie值，如果不存在则返回None
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                # 优先读取加密字段
                self._db._execute_sql(cursor, 
                    "SELECT value_encrypted, value FROM cookies WHERE id = ?", 
                    (cookie_id,)
                )
                result = cursor.fetchone()
                if not result:
                    return None
                
                encrypted_value, plain_value = result
                
                # 优先使用加密字段
                if encrypted_value:
                    try:
                        decrypted_value = decrypt(encrypted_value)
                        logger.debug(f"Cookie解密成功: {cookie_id}")
                        return decrypted_value
                    except EncryptionError as e:
                        logger.error(f"Cookie解密失败: {cookie_id}, {e}")
                        # 如果解密失败，尝试返回明文字段（向后兼容）
                        if plain_value:
                            logger.warning(f"使用明文Cookie（向后兼容）: {cookie_id}")
                            return plain_value
                        return None
                
                # 如果加密字段为空，返回明文字段（向后兼容）
                if plain_value:
                    logger.debug(f"使用明文Cookie（向后兼容）: {cookie_id}")
                    return plain_value
                
                return None
            except Exception as e:
                logger.error(f"获取Cookie失败: {e}")
                return None

    def get_all_cookies(self, user_id: int = None) -> Dict[str, str]:
        """获取所有Cookie（支持用户隔离，解密后）
        
        Args:
            user_id: 用户ID，如果为None则获取所有用户的Cookie
            
        Returns:
            Dict[str, str]: Cookie字典，键为cookie_id，值为解密后的cookie值
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if user_id is not None:
                    self._db._execute_sql(cursor, 
                        "SELECT id, value_encrypted, value FROM cookies WHERE user_id = ?", 
                        (user_id,)
                    )
                else:
                    self._db._execute_sql(cursor, 
                        "SELECT id, value_encrypted, value FROM cookies"
                    )
                
                result = {}
                for row in cursor.fetchall():
                    cookie_id, encrypted_value, plain_value = row
                    
                    # 优先使用加密字段
                    if encrypted_value:
                        try:
                            decrypted_value = decrypt(encrypted_value)
                            result[cookie_id] = decrypted_value
                        except EncryptionError as e:
                            logger.error(f"Cookie解密失败: {cookie_id}, {e}")
                            # 如果解密失败，尝试使用明文字段（向后兼容）
                            if plain_value:
                                logger.warning(f"使用明文Cookie（向后兼容）: {cookie_id}")
                                result[cookie_id] = plain_value
                    # 如果加密字段为空，使用明文字段（向后兼容）
                    elif plain_value:
                        result[cookie_id] = plain_value
                
                return result
            except Exception as e:
                logger.error(f"获取所有Cookie失败: {e}")
                return {}

    def get_cookie_by_id(self, cookie_id: str) -> Optional[Dict[str, str]]:
        """根据ID获取Cookie信息（解密后）
        
        Args:
            cookie_id: Cookie ID
            
        Returns:
            Optional[Dict[str, str]]: Cookie信息字典，包含id、cookies_str、value、created_at
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, 
                    "SELECT id, value_encrypted, value, created_at FROM cookies WHERE id = ?", 
                    (cookie_id,)
                )
                result = cursor.fetchone()
                if result:
                    cookie_id, encrypted_value, plain_value, created_at = result
                    
                    # 解密Cookie值
                    cookie_value = None
                    if encrypted_value:
                        try:
                            cookie_value = decrypt(encrypted_value)
                        except EncryptionError as e:
                            logger.error(f"Cookie解密失败: {cookie_id}, {e}")
                            # 如果解密失败，尝试使用明文字段（向后兼容）
                            if plain_value:
                                cookie_value = plain_value
                    elif plain_value:
                        cookie_value = plain_value
                    
                    return {
                        'id': cookie_id,
                        'cookies_str': cookie_value,
                        'value': cookie_value,
                        'created_at': created_at
                    }
                return None
            except Exception as e:
                logger.error(f"根据ID获取Cookie失败: {e}")
                return None

    def get_cookie_details(self, cookie_id: str) -> Optional[Dict[str, Any]]:
        """获取Cookie的详细信息，包括user_id和auto_confirm（解密后）
        
        Args:
            cookie_id: Cookie ID
            
        Returns:
            Optional[Dict[str, Any]]: Cookie详细信息字典，包含id、value、user_id、auto_confirm、created_at
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor,
                    "SELECT id, value_encrypted, value, user_id, auto_confirm, created_at FROM cookies WHERE id = ?",
                    (cookie_id,)
                )
                result = cursor.fetchone()
                if result:
                    cookie_id, encrypted_value, plain_value, user_id, auto_confirm, created_at = result
                    
                    # 解密Cookie值
                    cookie_value = None
                    if encrypted_value:
                        try:
                            cookie_value = decrypt(encrypted_value)
                        except EncryptionError as e:
                            logger.error(f"Cookie解密失败: {cookie_id}, {e}")
                            # 如果解密失败，尝试使用明文字段（向后兼容）
                            if plain_value:
                                cookie_value = plain_value
                    elif plain_value:
                        cookie_value = plain_value
                    
                    return {
                        'id': cookie_id,
                        'value': cookie_value,
                        'user_id': user_id,
                        'auto_confirm': bool(auto_confirm),
                        'created_at': created_at
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
