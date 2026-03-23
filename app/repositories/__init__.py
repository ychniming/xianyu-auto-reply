"""数据库管理模块

提供统一的数据库访问接口，组合多个仓储类
"""
from loguru import logger
from .base import BaseDB
from .cookie_repo import CookieRepository
from .keyword_repo import KeywordRepository
from .keyword_constants import VALID_MATCH_TYPES
from .user_repo import UserRepository
from .notification_repo import NotificationRepository
from .card_repo import CardRepository
from .item_repo import ItemRepository


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
        """保存AI回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO ai_reply_settings
                (cookie_id, ai_enabled, model_name, api_key, base_url,
                 max_discount_percent, max_discount_amount, max_bargain_rounds,
                 custom_prompts, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    cookie_id,
                    settings.get('ai_enabled', False),
                    settings.get('model_name', 'qwen-plus'),
                    settings.get('api_key', ''),
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
        """获取AI回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT ai_enabled, model_name, api_key, base_url,
                       max_discount_percent, max_discount_amount, max_bargain_rounds,
                       custom_prompts
                FROM ai_reply_settings WHERE cookie_id = ?
                ''', (cookie_id,))

                result = cursor.fetchone()
                if result:
                    return {
                        'ai_enabled': bool(result[0]),
                        'model_name': result[1],
                        'api_key': result[2],
                        'base_url': result[3],
                        'max_discount_percent': result[4],
                        'max_discount_amount': result[5],
                        'max_bargain_rounds': result[6],
                        'custom_prompts': result[7]
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
        """获取所有账号的AI回复设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT cookie_id, ai_enabled, model_name, api_key, base_url,
                       max_discount_percent, max_discount_amount, max_bargain_rounds,
                       custom_prompts
                FROM ai_reply_settings
                ''')

                result = {}
                for row in cursor.fetchall():
                    cookie_id = row[0]
                    result[cookie_id] = {
                        'ai_enabled': bool(row[1]),
                        'model_name': row[2],
                        'api_key': row[3],
                        'base_url': row[4],
                        'max_discount_percent': row[5],
                        'max_discount_amount': row[6],
                        'max_bargain_rounds': row[7],
                        'custom_prompts': row[8]
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
        """导入备份数据"""
        try:
            if 'cookies' in backup_data:
                for cookie_id, cookie_value in backup_data['cookies'].items():
                    self.save_cookie(cookie_id, cookie_value, user_id)

            if 'keywords' in backup_data:
                for cookie_id, kw_list in backup_data['keywords'].items():
                    self.save_keywords(cookie_id, kw_list)

            logger.info(f"备份导入成功")
            return True
        except Exception as e:
            logger.error(f"导入备份失败: {e}")
            return False

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


# 保持向后兼容的实例
db_manager = DBManager()
