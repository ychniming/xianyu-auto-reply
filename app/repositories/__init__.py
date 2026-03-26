"""数据库管理模块

提供统一的数据库访问接口，组合多个仓储类
"""
from loguru import logger
from .base import BaseDB
from .cookie_repo import CookieRepository
from .keyword_repo import KeywordRepository
from .user_repo import UserRepository
from .notification_repo import NotificationRepository
from .card_repo import CardRepository
from .item_repo import ItemRepository
from .transaction import TransactionManager, transactional, with_transaction_decorator
from app.utils.encryption import encrypt, decrypt, EncryptionError


class DBManager(BaseDB):
    """数据库管理类，组合所有仓储

    使用__getattr__实现动态委托，减少样板代码
    """

    # 仓储名称列表，用于动态委托
    _REPO_NAMES = ('cookies', 'keywords', 'users', 'notifications', 'cards', 'items')

    def __init__(self, db_path: str = None):
        """初始化数据库管理器"""
        super().__init__(db_path)

        # 初始化数据库连接
        self.init_db()

        # 初始化所有仓储
        self.cookies = CookieRepository(self)
        self.keywords = KeywordRepository(self)
        self.users = UserRepository(self)
        self.notifications = NotificationRepository(self)
        self.cards = CardRepository(self)
        self.items = ItemRepository(self)

        # 初始化事务管理器
        self.tx_manager = TransactionManager(self)

    def __getattr__(self, name):
        """动态委托到各个仓储

        当访问的属性不存在于DBManager本身时，
        自动查找各个仓储是否具有该属性并委托调用
        """
        for repo_name in self._REPO_NAMES:
            repo = getattr(self, repo_name, None)
            if repo and hasattr(repo, name):
                return getattr(repo, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # ==================== AI回复设置操作 ====================
    def save_ai_reply_settings(self, cookie_id: str, settings: dict) -> bool:
        """保存AI回复设置
        
        Args:
            cookie_id: 账号ID
            settings: 设置字典，包含api_key等字段
            
        Returns:
            bool: 是否保存成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                
                # 处理 API Key 加密
                api_key = settings.get('api_key', '')
                api_key_encrypted = ''
                
                # 如果提供了新的 API Key，则加密存储
                if api_key:
                    try:
                        api_key_encrypted = encrypt(api_key)
                        logger.debug(f"API Key 已加密: {cookie_id}")
                    except EncryptionError as e:
                        logger.error(f"API Key 加密失败: {e}")
                        return False
                
                cursor.execute('''
                INSERT OR REPLACE INTO ai_reply_settings
                (cookie_id, ai_enabled, model_name, api_key, api_key_encrypted, base_url,
                 max_discount_percent, max_discount_amount, max_bargain_rounds,
                 custom_prompts, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    cookie_id,
                    settings.get('ai_enabled', False),
                    settings.get('model_name', 'qwen-plus'),
                    '',  # api_key 字段留空，使用加密字段
                    api_key_encrypted,
                    settings.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
                    settings.get('max_discount_percent', 10),
                    settings.get('max_discount_amount', 100),
                    settings.get('max_bargain_rounds', 3),
                    settings.get('custom_prompts', '')
                ))
                self.conn.commit()
                logger.debug(f"AI回复设置保存成功: {cookie_id}")
                return True
            except Exception as e:
                logger.error(f"保存AI回复设置失败: {e}")
                self.conn.rollback()
                return False

    def get_ai_reply_settings(self, cookie_id: str) -> dict:
        """获取AI回复设置
        
        Args:
            cookie_id: 账号ID
            
        Returns:
            dict: AI回复设置字典，包含解密后的api_key
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT ai_enabled, model_name, api_key, api_key_encrypted, base_url,
                       max_discount_percent, max_discount_amount, max_bargain_rounds,
                       custom_prompts
                FROM ai_reply_settings WHERE cookie_id = ?
                ''', (cookie_id,))

                result = cursor.fetchone()
                if result:
                    # 优先使用加密字段
                    api_key = ''
                    api_key_encrypted = result[3]
                    
                    if api_key_encrypted:
                        # 解密 API Key
                        try:
                            api_key = decrypt(api_key_encrypted)
                        except EncryptionError as e:
                            logger.error(f"API Key 解密失败 {cookie_id}: {e}")
                            # 如果解密失败，尝试使用明文字段（向后兼容）
                            api_key = result[2] if result[2] else ''
                    else:
                        # 如果没有加密字段，使用明文字段（向后兼容）
                        api_key = result[2] if result[2] else ''
                    
                    return {
                        'ai_enabled': bool(result[0]),
                        'model_name': result[1],
                        'api_key': api_key,
                        'base_url': result[4],
                        'max_discount_percent': result[5],
                        'max_discount_amount': result[6],
                        'max_bargain_rounds': result[7],
                        'custom_prompts': result[8]
                    }
                else:
                    return {
                        'ai_enabled': False,
                        'model_name': 'qwen-plus',
                        'api_key': '',
                        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                        'max_discount_percent': 10,
                        'max_discount_amount': 100,
                        'max_bargain_rounds': 3,
                        'custom_prompts': ''
                    }
            except Exception as e:
                logger.error(f"获取AI回复设置失败: {e}")
                return {
                    'ai_enabled': False,
                    'model_name': 'qwen-plus',
                    'api_key': '',
                    'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                    'max_discount_percent': 10,
                    'max_discount_amount': 100,
                    'max_bargain_rounds': 3,
                    'custom_prompts': ''
                }

    def get_all_ai_reply_settings(self) -> dict:
        """获取所有账号的AI回复设置
        
        Returns:
            dict: 所有账号的AI回复设置字典，包含解密后的api_key
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT cookie_id, ai_enabled, model_name, api_key, api_key_encrypted, base_url,
                       max_discount_percent, max_discount_amount, max_bargain_rounds,
                       custom_prompts
                FROM ai_reply_settings
                ''')

                result = {}
                for row in cursor.fetchall():
                    cookie_id = row[0]
                    
                    # 优先使用加密字段
                    api_key = ''
                    api_key_encrypted = row[4]
                    
                    if api_key_encrypted:
                        # 解密 API Key
                        try:
                            api_key = decrypt(api_key_encrypted)
                        except EncryptionError as e:
                            logger.error(f"API Key 解密失败 {cookie_id}: {e}")
                            # 如果解密失败，尝试使用明文字段（向后兼容）
                            api_key = row[3] if row[3] else ''
                    else:
                        # 如果没有加密字段，使用明文字段（向后兼容）
                        api_key = row[3] if row[3] else ''
                    
                    result[cookie_id] = {
                        'ai_enabled': bool(row[1]),
                        'model_name': row[2],
                        'api_key': api_key,
                        'base_url': row[5],
                        'max_discount_percent': row[6],
                        'max_discount_amount': row[7],
                        'max_bargain_rounds': row[8],
                        'custom_prompts': row[9]
                    }

                return result
            except Exception as e:
                logger.error(f"获取所有AI回复设置失败: {e}")
                return {}

    # ==================== 默认回复操作 ====================
    def save_default_reply(self, cookie_id: str, enabled: bool, reply_content: str = None):
        """保存默认回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO default_replies (cookie_id, enabled, reply_content, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (cookie_id, enabled, reply_content))
                self.conn.commit()
                logger.debug(f"保存默认回复设置: {cookie_id} -> {'启用' if enabled else '禁用'}")
            except Exception as e:
                logger.error(f"保存默认回复设置失败: {e}")
                raise

    def get_default_reply(self, cookie_id: str) -> dict:
        """获取指定账号的默认回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT enabled, reply_content FROM default_replies WHERE cookie_id = ?
                ''', (cookie_id,))
                result = cursor.fetchone()
                if result:
                    enabled, reply_content = result
                    return {
                        'enabled': bool(enabled),
                        'reply_content': reply_content or ''
                    }
                return None
            except Exception as e:
                logger.error(f"获取默认回复设置失败: {e}")
                return None

    def get_all_default_replies(self) -> dict:
        """获取所有账号的默认回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT cookie_id, enabled, reply_content FROM default_replies')

                result = {}
                for row in cursor.fetchall():
                    cookie_id, enabled, reply_content = row
                    result[cookie_id] = {
                        'enabled': bool(enabled),
                        'reply_content': reply_content or ''
                    }

                return result
            except Exception as e:
                logger.error(f"获取所有默认回复设置失败: {e}")
                return {}

    def delete_default_reply(self, cookie_id: str) -> bool:
        """删除指定账号的默认回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._execute_sql(cursor, "DELETE FROM default_replies WHERE cookie_id = ?", (cookie_id,))
                self.conn.commit()
                logger.debug(f"删除默认回复设置: {cookie_id}")
                return True
            except Exception as e:
                logger.error(f"删除默认回复设置失败: {e}")
                self.conn.rollback()
                return False

    # ==================== AI对话操作 ====================
    def get_ai_conversation_context(self, chat_id: str, cookie_id: str, limit: int = 20) -> list:
        """Get AI conversation context for a chat session

        Args:
            chat_id: Chat session ID
            cookie_id: Account cookie ID
            limit: Maximum number of messages to retrieve

        Returns:
            list: List of conversation messages with 'role' and 'content' keys
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT role, content FROM ai_conversations
                    WHERE chat_id = ? AND cookie_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (chat_id, cookie_id, limit))

                results = cursor.fetchall()
                # Reverse order to get chronological sequence
                context = [{"role": row[0], "content": row[1]} for row in reversed(results)]
                return context
            except Exception as e:
                logger.error(f"Failed to get AI conversation context: {e}")
                return []

    def save_ai_conversation(self, chat_id: str, cookie_id: str, user_id: str,
                             item_id: str, role: str, content: str, intent: str = None) -> bool:
        """Save AI conversation record

        Args:
            chat_id: Chat session ID
            cookie_id: Account cookie ID
            user_id: User ID
            item_id: Item ID
            role: Message role ('user' or 'assistant')
            content: Message content
            intent: Message intent (optional)

        Returns:
            bool: True if saved successfully
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_conversations
                    (cookie_id, chat_id, user_id, item_id, role, content, intent)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (cookie_id, chat_id, user_id, item_id, role, content, intent))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to save AI conversation: {e}")
                self.conn.rollback()
                return False

    def get_ai_bargain_count(self, chat_id: str, cookie_id: str) -> int:
        """Get bargain count for a chat session

        Args:
            chat_id: Chat session ID
            cookie_id: Account cookie ID

        Returns:
            int: Number of bargain attempts
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM ai_conversations
                    WHERE chat_id = ? AND cookie_id = ? AND intent = 'price' AND role = 'user'
                ''', (chat_id, cookie_id))

                result = cursor.fetchone()
                return result[0] if result else 0
            except Exception as e:
                logger.error(f"Failed to get AI bargain count: {e}")
                return 0

    # ==================== 系统设置操作 ====================
    def get_all_system_settings(self) -> dict:
        """获取所有系统设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT key, value FROM system_settings')
                result = {}
                for row in cursor.fetchall():
                    result[row[0]] = row[1]
                return result
            except Exception as e:
                logger.error(f"获取所有系统设置失败: {e}")
                return {}

    # ==================== 备份导出导入 ====================
    def export_backup(self, user_id: int = None) -> dict:
        """导出备份数据"""
        try:
            cookies = self.get_all_cookies(user_id)
            keywords = self.get_all_keywords(user_id)
            cards = self.get_all_cards(user_id)
            delivery_rules = self.get_all_delivery_rules(user_id)
            default_replies = self.get_all_default_replies()
            ai_settings = self.get_all_ai_reply_settings()

            return {
                'version': '1.0',
                'timestamp': __import__('time').time(),
                'cookies': cookies,
                'keywords': keywords,
                'cards': cards,
                'delivery_rules': delivery_rules,
                'default_replies': default_replies,
                'ai_settings': ai_settings
            }
        except Exception as e:
            logger.error(f"导出备份失败: {e}")
            return {}

    def import_backup(self, backup_data: dict, user_id: int = None) -> bool:
        """导入备份数据

        使用事务确保导入操作的原子性，失败时自动回滚

        Args:
            backup_data: 备份数据字典
            user_id: 用户ID

        Returns:
            bool: 导入是否成功
        """
        try:
            # 使用事务包装所有导入操作
            with self.transaction:
                # 导入 Cookies
                if 'cookies' in backup_data:
                    for cookie_id, cookie_value in backup_data['cookies'].items():
                        if not self.cookies.save_cookie(cookie_id, cookie_value, user_id):
                            raise Exception(f"保存Cookie失败: {cookie_id}")
                        logger.debug(f"导入Cookie: {cookie_id}")

                # 导入关键词
                if 'keywords' in backup_data:
                    for cookie_id, kw_list in backup_data['keywords'].items():
                        if not self.keywords.save_keywords(cookie_id, kw_list):
                            raise Exception(f"保存关键词失败: {cookie_id}")
                        logger.debug(f"导入关键词: {cookie_id}, {len(kw_list)}条")

                # 导入卡券
                if 'cards' in backup_data:
                    for card_data in backup_data['cards']:
                        card_id = self.cards.create_card(
                            name=card_data.get('name'),
                            card_type=card_data.get('type'),
                            api_config=card_data.get('api_config'),
                            text_content=card_data.get('text_content'),
                            data_content=card_data.get('data_content'),
                            image_url=card_data.get('image_url'),
                            description=card_data.get('description'),
                            delay_seconds=card_data.get('delay_seconds', 0),
                            is_multi_spec=card_data.get('is_multi_spec', False),
                            spec_name=card_data.get('spec_name'),
                            spec_value=card_data.get('spec_value'),
                            user_id=user_id
                        )
                        if not card_id:
                            raise Exception(f"创建卡券失败: {card_data.get('name')}")
                        logger.debug(f"导入卡券: {card_data.get('name')} (ID: {card_id})")

                # 导入发货规则
                if 'delivery_rules' in backup_data:
                    for rule_data in backup_data['delivery_rules']:
                        rule_id = self.cards.create_delivery_rule(
                            keyword=rule_data.get('keyword'),
                            card_id=rule_data.get('card_id'),
                            delivery_count=rule_data.get('delivery_count', 1),
                            enabled=rule_data.get('enabled', True),
                            description=rule_data.get('description'),
                            user_id=user_id
                        )
                        if not rule_id:
                            raise Exception(f"创建发货规则失败: {rule_data.get('keyword')}")
                        logger.debug(f"导入发货规则: {rule_data.get('keyword')} (ID: {rule_id})")

                # 导入默认回复
                if 'default_replies' in backup_data:
                    for cookie_id, reply_data in backup_data['default_replies'].items():
                        self.save_default_reply(
                            cookie_id=cookie_id,
                            enabled=reply_data.get('enabled', False),
                            reply_content=reply_data.get('reply_content')
                        )
                        logger.debug(f"导入默认回复: {cookie_id}")

                # 导入AI设置
                if 'ai_settings' in backup_data:
                    for cookie_id, ai_data in backup_data['ai_settings'].items():
                        self.save_ai_reply_settings(cookie_id, ai_data)
                        logger.debug(f"导入AI设置: {cookie_id}")

                logger.info(f"备份导入成功")
                return True

        except Exception as e:
            logger.error(f"导入备份失败，已回滚所有操作: {e}")
            return False

    # ==================== Token 黑名单操作 ====================
    def add_token_to_blacklist(self, token: str, expires_at) -> bool:
        """添加 Token 到黑名单
        
        Args:
            token: 要加入黑名单的 Token
            expires_at: Token 过期时间（datetime 对象或时间戳）
        
        Returns:
            bool: 是否添加成功
        """
        from datetime import datetime
        
        with self.lock:
            try:
                cursor = self.conn.cursor()
                
                # 处理 expires_at 参数
                if isinstance(expires_at, datetime):
                    expires_at_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    expires_at_str = expires_at
                
                cursor.execute('''
                INSERT OR REPLACE INTO token_blacklist (token, created_at, expires_at)
                VALUES (?, CURRENT_TIMESTAMP, ?)
                ''', (token, expires_at_str))
                
                self.conn.commit()
                logger.debug(f"Token 已加入黑名单: {token[:20]}...")
                return True
            except Exception as e:
                logger.error(f"添加 Token 到黑名单失败: {e}")
                self.conn.rollback()
                return False

    def is_token_blacklisted(self, token: str) -> bool:
        """检查 Token 是否在黑名单中
        
        Args:
            token: 要检查的 Token
        
        Returns:
            bool: 是否在黑名单中
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT COUNT(*) FROM token_blacklist 
                WHERE token = ? AND expires_at > CURRENT_TIMESTAMP
                ''', (token,))
                
                result = cursor.fetchone()
                is_blacklisted = result[0] > 0 if result else False
                
                if is_blacklisted:
                    logger.debug(f"Token 在黑名单中: {token[:20]}...")
                
                return is_blacklisted
            except Exception as e:
                logger.error(f"检查 Token 黑名单失败: {e}")
                return False

    def cleanup_expired_blacklist_tokens(self) -> int:
        """清理过期的黑名单 Token
        
        Returns:
            int: 清理的记录数
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                DELETE FROM token_blacklist WHERE expires_at <= CURRENT_TIMESTAMP
                ''')
                
                deleted_count = cursor.rowcount
                self.conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"清理了 {deleted_count} 条过期的黑名单 Token")
                
                return deleted_count
            except Exception as e:
                logger.error(f"清理黑名单 Token 失败: {e}")
                self.conn.rollback()
                return 0

    # ==================== 特殊查询方法 ====================
    def get_all_keywords_with_type(self) -> dict:
        """获取所有账号的关键词（包含类型信息和新字段）

        Returns:
            dict: {cookie_id: [{'keyword': str, 'reply': str, 'item_id': str, 'type': str, 'image_url': str,
                               'match_type': str, 'priority': int, 'reply_mode': str, 'replies': str,
                               'trigger_count': int, 'conditions': str}, ...]}
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT cookie_id, keyword, reply, item_id, type, image_url,
                           match_type, priority, reply_mode, replies, trigger_count, conditions
                    FROM keywords
                ''')

                result = {}
                for row in cursor.fetchall():
                    cookie_id = row[0]
                    if cookie_id not in result:
                        result[cookie_id] = []
                    result[cookie_id].append({
                        'keyword': row[1],
                        'reply': row[2],
                        'item_id': row[3],
                        'type': row[4] or 'text',
                        'image_url': row[5],
                        'match_type': row[6] or 'contains',
                        'priority': row[7] or 0,
                        'reply_mode': row[8] or 'single',
                        'replies': row[9],
                        'trigger_count': row[10] or 0,
                        'conditions': row[11]
                    })

                return result
            except Exception as e:
                logger.error(f"获取所有关键词失败: {e}")
                return {}

    # ==================== 事务管理方法 ====================
    def begin_transaction(self) -> None:
        """开始事务

        如果已经在事务中，则创建保存点支持嵌套事务
        """
        self.tx_manager.begin_transaction()

    def commit(self) -> None:
        """提交事务

        如果在嵌套事务中，则释放保存点
        """
        self.tx_manager.commit()

    def rollback(self) -> None:
        """回滚事务

        如果在嵌套事务中，则回滚到保存点
        """
        self.tx_manager.rollback()

    @property
    def transaction(self):
        """获取事务上下文管理器

        Example:
            with db_manager.transaction:
                db_manager.save_cookie(...)
                db_manager.save_keywords(...)
        """
        return self.tx_manager.with_transaction()


# 保持向后兼容的实例
db_manager = DBManager()

# 导出事务相关类和函数
__all__ = [
    'DBManager',
    'db_manager',
    'TransactionManager',
    'transactional',
    'with_transaction_decorator'
]
