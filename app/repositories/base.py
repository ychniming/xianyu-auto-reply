"""数据库基础模块

包含数据库初始化、连接管理等基础功能
"""
import sqlite3
import os
import threading
from typing import Optional
from loguru import logger

from .migrations import DatabaseMigrator, DatabaseUpgrader


class BaseDB:
    """数据库基础类，提供初始化和连接管理"""

    def __init__(self, db_path: str = None):
        """初始化数据库连接和表结构"""
        # 支持环境变量配置数据库路径
        if db_path is None:
            db_path = os.getenv('DB_PATH', 'xianyu_data.db')
        
        # 如果是相对路径，转换为项目根目录的绝对路径
        if not os.path.isabs(db_path):
            # 获取项目根目录（base.py 的父目录的父目录）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # 如果路径中已经包含 data 目录，直接使用项目根目录
            if os.path.basename(os.path.dirname(db_path)) == 'data':
                db_path = os.path.join(project_root, db_path)
            else:
                db_path = os.path.join(project_root, 'data', db_path)
            logger.info(f"使用项目数据目录：{os.path.dirname(db_path)}")

        # 确保数据目录存在并有正确权限
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, mode=0o755, exist_ok=True)
                logger.info(f"创建数据目录：{db_dir}")
            except PermissionError as e:
                logger.error(f"创建数据目录失败，权限不足：{e}")
                db_path = os.path.basename(db_path)
                logger.warning(f"使用当前目录作为数据库路径：{db_path}")
            except Exception as e:
                logger.error(f"创建数据目录失败：{e}")
                raise

        # 检查目录权限
        if db_dir and os.path.exists(db_dir):
            if not os.access(db_dir, os.W_OK):
                logger.error(f"数据目录没有写权限：{db_dir}")
                db_path = os.path.basename(db_path)
                logger.warning(f"使用当前目录作为数据库路径：{db_path}")

        self.db_path = db_path
        logger.info(f"数据库路径：{self.db_path}")
        self.conn: Optional[sqlite3.Connection] = None
        self.lock = threading.RLock()

        # SQL日志配置
        self.sql_log_enabled = True
        self.sql_log_level = 'INFO'

        if os.getenv('SQL_LOG_ENABLED'):
            self.sql_log_enabled = os.getenv('SQL_LOG_ENABLED', 'true').lower() == 'true'
        if os.getenv('SQL_LOG_LEVEL'):
            self.sql_log_level = os.getenv('SQL_LOG_LEVEL', 'INFO').upper()

        logger.info(f"SQL日志已启用，日志级别: {self.sql_log_level}")

    def init_db(self) -> None:
        """初始化数据库表结构"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()

            # 创建用户表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建邮箱验证码表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建图形验证码表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS captcha_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建cookies表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cookies (
                id TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                auto_confirm INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            ''')

            # 创建keywords表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                reply TEXT,
                item_id TEXT,
                type TEXT DEFAULT 'text',
                image_url TEXT,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            # 创建cookie_status表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cookie_status (
                cookie_id TEXT PRIMARY KEY,
                enabled BOOLEAN DEFAULT TRUE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            # 创建AI回复配置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_reply_settings (
                cookie_id TEXT PRIMARY KEY,
                ai_enabled BOOLEAN DEFAULT FALSE,
                model_name TEXT DEFAULT 'qwen-plus',
                api_key TEXT,
                api_key_encrypted TEXT,
                base_url TEXT DEFAULT 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                max_discount_percent INTEGER DEFAULT 10,
                max_discount_amount INTEGER DEFAULT 100,
                max_bargain_rounds INTEGER DEFAULT 3,
                custom_prompts TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            # 创建AI对话历史表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                bargain_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies (id) ON DELETE CASCADE
            )
            ''')

            # 创建AI商品信息缓存表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_item_cache (
                item_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                price REAL,
                description TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建卡券表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('api', 'text', 'data', 'image')),
                api_config TEXT,
                text_content TEXT,
                data_content TEXT,
                image_url TEXT,
                description TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                delay_seconds INTEGER DEFAULT 0,
                is_multi_spec BOOLEAN DEFAULT FALSE,
                spec_name TEXT,
                spec_value TEXT,
                user_id INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')

            # 创建商品信息表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                item_title TEXT,
                item_description TEXT,
                item_category TEXT,
                item_price TEXT,
                item_detail TEXT,
                is_multi_spec BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE,
                UNIQUE(cookie_id, item_id)
            )
            ''')

            # 创建自动发货规则表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                card_id INTEGER NOT NULL,
                user_id INTEGER DEFAULT 1,
                delivery_count INTEGER DEFAULT 1,
                enabled BOOLEAN DEFAULT TRUE,
                description TEXT,
                delivery_times INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
            )
            ''')

            # 创建默认回复表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS default_replies (
                cookie_id TEXT PRIMARY KEY,
                enabled BOOLEAN DEFAULT FALSE,
                reply_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            # 创建通知渠道表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                user_id INTEGER DEFAULT 1,
                type TEXT NOT NULL CHECK (type IN ('qq')),
                config TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建系统设置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建消息通知配置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE,
                FOREIGN KEY (channel_id) REFERENCES notification_channels(id) ON DELETE CASCADE,
                UNIQUE(cookie_id, channel_id)
            )
            ''')

            # 创建用户设置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, key)
            )
            ''')

            # 创建会话Token表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            ''')

            # 创建Token黑名单表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_blacklist (
                token TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
            ''')

            # 创建索引
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires_at ON token_blacklist(expires_at)
            ''')

            # Create indexes for keywords table
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_keywords_cookie_id ON keywords(cookie_id)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_keywords_cookie_keyword ON keywords(cookie_id, keyword)
            ''')

            # Create indexes for other commonly queried tables
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cookies_user_id ON cookies(user_id)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_delivery_rules_card_id ON delivery_rules(card_id)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_item_info_cookie_id ON item_info(cookie_id)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_item_info_item_id ON item_info(item_id)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_conversations_cookie_id ON ai_conversations(cookie_id)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_conversations_chat_id ON ai_conversations(chat_id)
            ''')

            # 插入默认系统设置
            cursor.execute('''
            INSERT OR IGNORE INTO system_settings (key, value, description) VALUES
            ('theme_color', 'blue', '主题颜色')
            ''')

            # 执行数据库迁移和升级
            migrator = DatabaseMigrator(self)
            upgrader = DatabaseUpgrader(self)
            
            upgrader.check_and_upgrade(cursor)
            migrator.run_migrations(cursor)

            self.conn.commit()
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            self.conn.rollback()
            raise

    def close(self) -> None:
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self.conn

    def _log_sql(self, sql: str, params: tuple = None, operation: str = "EXECUTE") -> None:
        """记录SQL执行日志"""
        if not self.sql_log_enabled:
            return

        params_str = ""
        if params:
            if isinstance(params, (list, tuple)):
                if len(params) > 0:
                    formatted_params = []
                    for param in params:
                        if isinstance(param, str) and len(param) > 100:
                            formatted_params.append(f"{param[:100]}...")
                        else:
                            formatted_params.append(repr(param))
                    params_str = f" | 参数: [{', '.join(formatted_params)}]"

        formatted_sql = ' '.join(sql.split())
        log_message = f"SQL {operation}: {formatted_sql}{params_str}"

        if self.sql_log_level == 'DEBUG':
            logger.debug(log_message)
        elif self.sql_log_level == 'INFO':
            logger.info(log_message)
        elif self.sql_log_level == 'WARNING':
            logger.warning(log_message)
        else:
            logger.debug(log_message)

    def _execute_sql(self, cursor, sql: str, params: tuple = None):
        """执行SQL并记录日志"""
        self._log_sql(sql, params, "EXECUTE")
        if params:
            return cursor.execute(sql, params)
        else:
            return cursor.execute(sql)

    def _executemany_sql(self, cursor, sql: str, params_list) -> None:
        """批量执行SQL并记录日志"""
        self._log_sql(sql, f"批量执行 {len(params_list)} 条记录", "EXECUTEMANY")
        cursor.executemany(sql, params_list)

    def get_system_setting(self, key: str) -> Optional[str]:
        """获取系统设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT value FROM system_settings WHERE key = ?', (key,))
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                logger.error(f"获取系统设置失败: {e}")
                return None

    def set_system_setting(self, key: str, value: str, description: str = None) -> bool:
        """设置系统设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO system_settings (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (key, value, description))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"设置系统设置失败: {e}")
                return False
