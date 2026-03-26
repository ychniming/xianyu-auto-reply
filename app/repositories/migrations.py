"""数据库迁移模块

提供数据库版本升级和迁移功能
"""
import hashlib
import sqlite3
from typing import Optional
from loguru import logger
from packaging.version import Version


class DatabaseMigrator:
    """数据库迁移器 - 处理数据库版本升级"""

    def __init__(self, db_manager):
        """初始化迁移器

        Args:
            db_manager: DBManager实例
        """
        self._db = db_manager
        self.conn = db_manager.conn
        self.lock = db_manager.lock

    def run_migrations(self, cursor) -> None:
        """执行数据库迁移"""
        try:
            cursor.execute("PRAGMA table_info(cards)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'image_url' not in columns:
                logger.info("添加cards表的image_url列...")
                cursor.execute("ALTER TABLE cards ADD COLUMN image_url TEXT")
                logger.info("数据库迁移完成：添加image_url列")

            self._update_cards_table_constraints(cursor)
            self._create_cookies_indexes(cursor)
        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")

    def _update_cards_table_constraints(self, cursor) -> None:
        """更新cards表的CHECK约束以支持image类型"""
        try:
            cursor.execute('''
                INSERT INTO cards (name, type, user_id)
                VALUES ('__test_image_constraint__', 'image', 1)
            ''')
            cursor.execute("DELETE FROM cards WHERE name = '__test_image_constraint__'")
            logger.info("cards表约束检查通过，支持image类型")
        except Exception as e:
            if "CHECK constraint failed" in str(e) or "constraint" in str(e).lower():
                logger.info("检测到旧的CHECK约束，开始更新cards表...")

                try:
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cards_new (
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

                    cursor.execute('''
                    INSERT INTO cards_new (id, name, type, api_config, text_content, data_content, image_url,
                                          description, enabled, delay_seconds, is_multi_spec, spec_name, spec_value,
                                          user_id, created_at, updated_at)
                    SELECT id, name, type, api_config, text_content, data_content, image_url,
                           description, enabled, delay_seconds, is_multi_spec, spec_name, spec_value,
                           user_id, created_at, updated_at
                    FROM cards
                    ''')

                    cursor.execute("DROP TABLE cards")
                    cursor.execute("ALTER TABLE cards_new RENAME TO cards")
                    logger.info("cards表约束更新完成，现在支持image类型")
                except Exception as rebuild_error:
                    logger.error(f"重建cards表失败: {rebuild_error}")
                    try:
                        cursor.execute("DROP TABLE IF EXISTS cards_new")
                    except sqlite3.OperationalError:
                        pass
            else:
                logger.error(f"检查cards表约束时出现未知错误: {e}")

    def _create_cookies_indexes(self, cursor) -> None:
        """为 cookies 表创建索引以提高查询性能"""
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_cookies_user_id'")
            if cursor.fetchone():
                logger.info("cookies 表的 user_id 索引已存在，跳过")
                return

            logger.info("开始为 cookies 表创建 user_id 索引...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cookies_user_id ON cookies(user_id)")
            logger.info("cookies 表的 user_id 索引创建成功")

            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_cookie_status_cookie_id'")
            if cursor.fetchone():
                logger.info("cookie_status 表的 cookie_id 索引已存在，跳过")
                return

            logger.info("开始为 cookie_status 表创建 cookie_id 索引...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cookie_status_cookie_id ON cookie_status(cookie_id)")
            logger.info("cookie_status 表的 cookie_id 索引创建成功")
        except Exception as e:
            logger.error(f"创建索引失败: {e}")

    def _migrate_keywords_table_constraints(self, cursor) -> None:
        """迁移keywords表的约束"""
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_keywords_unique_with_item'")
            if cursor.fetchone():
                logger.info("keywords表约束已经迁移过，跳过")
                return

            logger.info("开始迁移keywords表约束...")

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords_temp (
                cookie_id TEXT,
                keyword TEXT,
                reply TEXT,
                item_id TEXT,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            cursor.execute('''
            INSERT INTO keywords_temp (cookie_id, keyword, reply, item_id)
            SELECT cookie_id, keyword, reply, item_id FROM keywords
            ''')

            cursor.execute('DROP TABLE keywords')
            cursor.execute('ALTER TABLE keywords_temp RENAME TO keywords')

            cursor.execute('''
            CREATE UNIQUE INDEX idx_keywords_unique_no_item
            ON keywords(cookie_id, keyword)
            WHERE item_id IS NULL OR item_id = ''
            ''')

            cursor.execute('''
            CREATE UNIQUE INDEX idx_keywords_unique_with_item
            ON keywords(cookie_id, keyword, item_id)
            WHERE item_id IS NOT NULL AND item_id != ''
            ''')

            logger.info("keywords表约束迁移完成")
        except Exception as e:
            logger.error(f"迁移keywords表约束失败: {e}")
            try:
                cursor.execute('DROP TABLE IF EXISTS keywords_temp')
            except sqlite3.OperationalError:
                pass
            raise


class DatabaseUpgrader:
    """数据库升级器 - 处理数据库版本升级"""

    def __init__(self, db_manager):
        """初始化升级器

        Args:
            db_manager: DBManager实例
        """
        self._db = db_manager
        self.conn = db_manager.conn
        self.lock = db_manager.lock

    def check_and_upgrade(self, cursor) -> None:
        """检查数据库版本并执行必要的升级

        使用版本迭代循环自动执行所有未完成的升级，
        大幅减少重复代码。
        """
        try:
            current_version_str = self._get_system_setting("db_version") or "1.0"
            current_version = Version(current_version_str)
            logger.info(f"当前数据库版本: {current_version_str}")

            upgrade_mapping = {
                Version("1.0"): (self._upgrade_to_1_0, "1.0"),
                Version("1.1"): (self._upgrade_to_1_1, "1.1"),
                Version("1.2"): (self._upgrade_to_1_2, "1.2"),
                Version("1.3"): (self._upgrade_to_1_3, "1.3"),
                Version("1.4"): (self._upgrade_to_1_4, "1.4"),
                Version("1.5"): (self._upgrade_to_1_5, "1.5"),
            }

            target_versions = sorted(upgrade_mapping.keys())
            for target_version in target_versions:
                if current_version < target_version:
                    upgrade_func, version_str = upgrade_mapping[target_version]
                    logger.info(f"开始升级数据库到版本{version_str}...")
                    upgrade_func(cursor)
                    self._set_system_setting("db_version", version_str, "数据库版本号")
                    logger.info(f"数据库升级到版本{version_str}完成")

            self._migrate_legacy_data(cursor)
        except Exception as e:
            logger.error(f"数据库版本检查或升级失败: {e}")
            raise

    def _get_system_setting(self, key: str) -> Optional[str]:
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

    def _set_system_setting(self, key: str, value: str, description: str = None) -> bool:
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

    def _upgrade_to_1_0(self, cursor) -> None:
        """升级到版本1.0"""
        self._update_admin_user_id(cursor)

    def _upgrade_to_1_1(self, cursor) -> None:
        """升级到版本1.1"""
        self._upgrade_notification_channels_table(cursor)

    def _upgrade_to_1_2(self, cursor) -> None:
        """升级到版本1.2"""
        self._upgrade_notification_channels_types(cursor)

    def _upgrade_to_1_3(self, cursor) -> None:
        """升级到版本1.3"""
        self._upgrade_keywords_table_for_image_support(cursor)

    def _upgrade_to_1_4(self, cursor) -> None:
        """升级到版本1.4"""
        self._upgrade_keywords_table_for_advanced_features(cursor)

    def _upgrade_to_1_5(self, cursor) -> None:
        """升级到版本1.5 - 为keywords表添加主键"""
        try:
            logger.info("开始为keywords表添加主键...")

            # Check if id column already exists
            cursor.execute("PRAGMA table_info(keywords)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'id' in columns:
                logger.info("keywords表已存在id主键，跳过迁移")
                return

            # Get existing data count
            cursor.execute("SELECT COUNT(*) FROM keywords")
            count = cursor.fetchone()[0]
            logger.info(f"keywords表现有数据: {count}条")

            # Create new table with primary key
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                reply TEXT,
                item_id TEXT,
                type TEXT DEFAULT 'text',
                image_url TEXT,
                match_type TEXT DEFAULT 'contains',
                priority INTEGER DEFAULT 0,
                reply_mode TEXT DEFAULT 'single',
                replies TEXT,
                trigger_count INTEGER DEFAULT 0,
                conditions TEXT,
                sequence_index INTEGER DEFAULT 0,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id) ON DELETE CASCADE
            )
            ''')

            # Migrate existing data
            if count > 0:
                cursor.execute('''
                INSERT INTO keywords_new 
                    (cookie_id, keyword, reply, item_id, type, image_url,
                     match_type, priority, reply_mode, replies, trigger_count, 
                     conditions, sequence_index)
                SELECT 
                    cookie_id, keyword, reply, item_id, type, image_url,
                    COALESCE(match_type, 'contains'), 
                    COALESCE(priority, 0), 
                    COALESCE(reply_mode, 'single'), 
                    replies, 
                    COALESCE(trigger_count, 0), 
                    conditions, 
                    COALESCE(sequence_index, 0)
                FROM keywords
                ''')
                logger.info(f"成功迁移 {count} 条keywords数据")

            # Drop old table and rename new table
            cursor.execute("DROP TABLE keywords")
            cursor.execute("ALTER TABLE keywords_new RENAME TO keywords")

            # Recreate indexes
            cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_keywords_unique_no_item
            ON keywords(cookie_id, keyword)
            WHERE item_id IS NULL OR item_id = ''
            ''')

            cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_keywords_unique_with_item
            ON keywords(cookie_id, keyword, item_id)
            WHERE item_id IS NOT NULL AND item_id != ''
            ''')

            logger.info("keywords表主键迁移完成")
        except Exception as e:
            logger.error(f"升级keywords表主键失败: {e}")
            # Clean up temp table if exists
            try:
                cursor.execute("DROP TABLE IF EXISTS keywords_new")
            except sqlite3.OperationalError:
                pass
            raise

    def _update_admin_user_id(self, cursor) -> None:
        """更新admin用户ID"""
        try:
            logger.info("开始更新admin用户ID...")
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
            admin_exists = cursor.fetchone()[0] > 0

            if not admin_exists:
                default_password_hash = hashlib.sha256("admin123".encode()).hexdigest()
                cursor.execute('''
                INSERT INTO users (username, email, password_hash) VALUES
                ('admin', 'admin@localhost', ?)
                ''', (default_password_hash,))
                logger.info("创建默认admin用户，请及时修改密码")

            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            admin_user = cursor.fetchone()
            if admin_user:
                admin_user_id = admin_user[0]

                try:
                    cursor.execute("SELECT user_id FROM cookies LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE cookies ADD COLUMN user_id INTEGER")
                    cursor.execute("UPDATE cookies SET user_id = ? WHERE user_id IS NULL", (admin_user_id,))

                try:
                    cursor.execute("SELECT auto_confirm FROM cookies LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE cookies ADD COLUMN auto_confirm INTEGER DEFAULT 1")
                    cursor.execute("UPDATE cookies SET auto_confirm = 1 WHERE auto_confirm IS NULL")

                try:
                    cursor.execute("SELECT user_id FROM delivery_rules LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE delivery_rules ADD COLUMN user_id INTEGER")
                    cursor.execute("UPDATE delivery_rules SET user_id = ? WHERE user_id IS NULL", (admin_user_id,))

                try:
                    cursor.execute("SELECT user_id FROM notification_channels LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE notification_channels ADD COLUMN user_id INTEGER")
                    cursor.execute("UPDATE notification_channels SET user_id = ? WHERE user_id IS NULL", (admin_user_id,))

                try:
                    cursor.execute("SELECT type FROM email_verifications LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE email_verifications ADD COLUMN type TEXT DEFAULT 'register'")
                    cursor.execute("UPDATE email_verifications SET type = 'register' WHERE type IS NULL")

                try:
                    cursor.execute("SELECT is_multi_spec FROM cards LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE cards ADD COLUMN is_multi_spec BOOLEAN DEFAULT FALSE")
                    cursor.execute("ALTER TABLE cards ADD COLUMN spec_name TEXT")
                    cursor.execute("ALTER TABLE cards ADD COLUMN spec_value TEXT")
                    logger.info("为cards表添加多规格字段")

                try:
                    cursor.execute("SELECT is_multi_spec FROM item_info LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE item_info ADD COLUMN is_multi_spec BOOLEAN DEFAULT FALSE")
                    logger.info("为item_info表添加多规格字段")

            logger.info("admin用户ID更新完成")
        except Exception as e:
            logger.error(f"更新admin用户ID失败: {e}")
            raise

    def _upgrade_notification_channels_table(self, cursor) -> None:
        """升级notification_channels表"""
        try:
            logger.info("开始升级notification_channels表...")

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_channels'")
            if not cursor.fetchone():
                logger.info("notification_channels表不存在，无需升级")
                return

            cursor.execute("SELECT COUNT(*) FROM notification_channels")
            count = cursor.fetchone()[0]

            cursor.execute("DROP TABLE IF EXISTS notification_channels_new")

            cursor.execute('''
            CREATE TABLE notification_channels_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('qq','ding_talk')),
                config TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            if count > 0:
                cursor.execute("SELECT * FROM notification_channels")
                existing_data = cursor.fetchall()

                for row in existing_data:
                    old_type = row[3] if len(row) > 3 else 'qq'
                    type_mapping = {
                        'dingtalk': 'ding_talk',
                        'ding_talk': 'ding_talk',
                        'qq': 'qq',
                        'email': 'qq',
                        'webhook': 'qq',
                        'wechat': 'qq',
                        'telegram': 'qq'
                    }
                    new_type = type_mapping.get(old_type, 'qq')

                    cursor.execute('''
                    INSERT INTO notification_channels_new
                    (id, name, user_id, type, config, enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row[0], row[1], row[2], new_type,
                        row[4] if len(row) > 4 else '{}',
                        row[5] if len(row) > 5 else True,
                        row[6] if len(row) > 6 else None,
                        row[7] if len(row) > 7 else None
                    ))

            cursor.execute("DROP TABLE notification_channels")
            cursor.execute("ALTER TABLE notification_channels_new RENAME TO notification_channels")
            logger.info("notification_channels表升级完成")
        except Exception as e:
            logger.error(f"升级notification_channels表失败: {e}")
            raise

    def _upgrade_notification_channels_types(self, cursor) -> None:
        """升级notification_channels表支持更多渠道类型"""
        try:
            logger.info("开始升级notification_channels表支持更多渠道类型...")

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_channels'")
            if not cursor.fetchone():
                return

            cursor.execute("SELECT COUNT(*) FROM notification_channels")
            count = cursor.fetchone()[0]

            existing_data = []
            if count > 0:
                cursor.execute("SELECT * FROM notification_channels")
                existing_data = cursor.fetchall()

            cursor.execute('''
            CREATE TABLE notification_channels_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('qq','ding_talk','dingtalk','email','webhook','wechat','telegram')),
                config TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            if existing_data:
                for row in existing_data:
                    old_type = row[3] if len(row) > 3 else 'qq'
                    type_mapping = {
                        'ding_talk': 'dingtalk',
                        'dingtalk': 'dingtalk',
                        'qq': 'qq',
                        'email': 'email',
                        'webhook': 'webhook',
                        'wechat': 'wechat',
                        'telegram': 'telegram'
                    }
                    new_type = type_mapping.get(old_type, 'qq')

                    cursor.execute('''
                    INSERT INTO notification_channels_new
                    (id, name, user_id, type, config, enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row[0], row[1], row[2], new_type,
                        row[4] if len(row) > 4 else '{}',
                        row[5] if len(row) > 5 else True,
                        row[6] if len(row) > 6 else None,
                        row[7] if len(row) > 7 else None
                    ))

            cursor.execute("DROP TABLE notification_channels")
            cursor.execute("ALTER TABLE notification_channels_new RENAME TO notification_channels")
            logger.info("notification_channels表类型升级完成")
        except Exception as e:
            logger.error(f"升级notification_channels表类型失败: {e}")
            raise

    def _upgrade_keywords_table_for_image_support(self, cursor) -> None:
        """升级keywords表支持图片类型"""
        try:
            cursor.execute("PRAGMA table_info(keywords)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'type' not in columns:
                cursor.execute("ALTER TABLE keywords ADD COLUMN type TEXT DEFAULT 'text'")
            if 'image_url' not in columns:
                cursor.execute("ALTER TABLE keywords ADD COLUMN image_url TEXT")
            if 'item_id' not in columns:
                cursor.execute("ALTER TABLE keywords ADD COLUMN item_id TEXT")
            logger.info("keywords表图片支持升级完成")
        except Exception as e:
            logger.error(f"升级keywords表图片支持失败: {e}")

    def _upgrade_keywords_table_for_advanced_features(self, cursor) -> None:
        """升级keywords表支持高级功能"""
        try:
            cursor.execute("PRAGMA table_info(keywords)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'match_type' not in columns:
                logger.info("正在为 keywords 表添加 match_type 列...")
                cursor.execute("ALTER TABLE keywords ADD COLUMN match_type TEXT DEFAULT 'contains'")

            if 'priority' not in columns:
                logger.info("正在为 keywords 表添加 priority 列...")
                cursor.execute("ALTER TABLE keywords ADD COLUMN priority INTEGER DEFAULT 0")

            if 'reply_mode' not in columns:
                logger.info("正在为 keywords 表添加 reply_mode 列...")
                cursor.execute("ALTER TABLE keywords ADD COLUMN reply_mode TEXT DEFAULT 'single'")

            if 'replies' not in columns:
                logger.info("正在为 keywords 表添加 replies 列...")
                cursor.execute("ALTER TABLE keywords ADD COLUMN replies TEXT")

            if 'trigger_count' not in columns:
                logger.info("正在为 keywords 表添加 trigger_count 列...")
                cursor.execute("ALTER TABLE keywords ADD COLUMN trigger_count INTEGER DEFAULT 0")

            if 'conditions' not in columns:
                logger.info("正在为 keywords 表添加 conditions 列...")
                cursor.execute("ALTER TABLE keywords ADD COLUMN conditions TEXT")

            if 'sequence_index' not in columns:
                logger.info("正在为 keywords 表添加 sequence_index 列...")
                cursor.execute("ALTER TABLE keywords ADD COLUMN sequence_index INTEGER DEFAULT 0")

            logger.info("keywords表高级功能升级完成")
        except Exception as e:
            logger.error(f"升级keywords表高级功能失败: {e}")
            raise

    def _migrate_legacy_data(self, cursor) -> bool:
        """迁移遗留数据"""
        try:
            logger.info("开始检查和迁移遗留数据...")

            legacy_tables = [
                'old_notification_channels',
                'legacy_delivery_rules',
                'old_keywords',
                'backup_cookies'
            ]

            for table_name in legacy_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone():
                    logger.info(f"发现遗留表: {table_name}，开始迁移数据...")
                    self._migrate_table_data(cursor, table_name)

            logger.info("遗留数据迁移完成")
            return True
        except Exception as e:
            logger.error(f"迁移遗留数据失败: {e}")
            return False

    def _migrate_table_data(self, cursor, table_name: str) -> None:
        """迁移指定表的数据"""
        try:
            if table_name == 'old_notification_channels':
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]

                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name}")
                    old_data = cursor.fetchall()

                    for row in old_data:
                        cursor.execute('''
                        INSERT OR IGNORE INTO notification_channels
                        (name, user_id, type, config, enabled)
                        VALUES (?, ?, ?, ?, ?)
                        ''', (
                            row[1] if len(row) > 1 else f"迁移渠道_{row[0]}",
                            row[2] if len(row) > 2 else 1,
                            self._normalize_channel_type(row[3] if len(row) > 3 else 'qq'),
                            row[4] if len(row) > 4 else '{}',
                            row[5] if len(row) > 5 else True
                        ))

                    logger.info(f"成功迁移 {count} 条通知渠道数据")
                    cursor.execute(f"DROP TABLE {table_name}")
                    logger.info(f"已删除遗留表: {table_name}")
        except Exception as e:
            logger.error(f"迁移表 {table_name} 数据失败: {e}")

    def _normalize_channel_type(self, old_type: str) -> str:
        """标准化通知渠道类型"""
        type_mapping = {
            'ding_talk': 'dingtalk',
            'dingtalk': 'dingtalk',
            'qq': 'qq',
            'email': 'email',
            'webhook': 'webhook',
            'wechat': 'wechat',
            'telegram': 'telegram',
            'dingding': 'dingtalk',
            'weixin': 'wechat',
            'tg': 'telegram'
        }
        return type_mapping.get(old_type.lower(), 'qq')
