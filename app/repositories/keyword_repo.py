"""Keyword仓储模块

提供关键字数据的增删改查操作
"""
import sqlite3
from typing import List, Tuple, Dict, Optional, Any, TYPE_CHECKING
from loguru import logger

from .keyword_constants import (
    normalize_match_type,
    normalize_priority,
)

if TYPE_CHECKING:
    from .keyword_cache import KeywordCacheManager


class KeywordRepository:
    """Keyword数据访问层"""

    def __init__(self, db_manager):
        """初始化仓储

        Args:
            db_manager: DBManager实例引用
        """
        self._db = db_manager
        self.conn = db_manager.conn
        self.lock = db_manager.lock
        self._cache_manager: Optional['KeywordCacheManager'] = None

    @property
    def _cache(self) -> 'KeywordCacheManager':
        """获取缓存管理器（延迟初始化）"""
        if self._cache_manager is None:
            from .keyword_cache import KeywordCacheManager
            self._cache_manager = KeywordCacheManager(self)
        return self._cache_manager

    def _get_keywords_with_type_unlocked(self, cookie_id: str) -> List[Dict[str, Any]]:
        """获取指定Cookie的关键字列表（包含类型信息）- 不加锁版本

        仅供在已持有锁的方法内部调用，避免重复加锁。

        Args:
            cookie_id: 账号ID

        Returns:
            List[Dict[str, Any]]: 关键词列表
        """
        return self._cache._get_keywords_with_type_unlocked(cookie_id)

    def _refresh_matcher_cache_unlocked(self, cookie_id: str) -> bool:
        """刷新关键词匹配器缓存 - 不在锁内调用

        当关键词发生变更时调用此方法，重建对应账号的自动机。
        此方法会获取锁，不应在已持有锁的上下文中调用。

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 刷新是否成功
        """
        return self._cache.refresh_cache_unlocked(cookie_id)

    def _refresh_matcher_cache_locked(self, cookie_id: str) -> bool:
        """刷新关键词匹配器缓存 - 在锁内调用

        当关键词发生变更时调用此方法，重建对应账号的自动机。
        此方法不加锁，必须在已持有锁的上下文中调用。

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 刷新是否成功
        """
        return self._cache._refresh_cache_locked(cookie_id)

    def save_keywords(self, cookie_id: str, keywords: List[Tuple[str, str]]) -> bool:
        """保存关键字列表，先删除旧数据再插入新数据（向后兼容方法）"""
        keywords_with_item_id = [(keyword, reply, None) for keyword, reply in keywords]
        return self.save_keywords_with_item_id(cookie_id, keywords_with_item_id)

    def save_keywords_with_item_id(self, cookie_id: str, keywords: List[Tuple[str, str, str]]) -> bool:
        """保存关键字列表（包含商品ID），先删除旧数据再插入新数据（向后兼容方法）"""
        # 转换为新格式，使用默认值
        keywords_advanced = []
        for keyword, reply, item_id in keywords:
            keywords_advanced.append({
                'keyword': keyword,
                'reply': reply,
                'item_id': item_id,
                'match_type': 'contains',
                'priority': 0,
                'reply_mode': 'single',
                'replies': None,
                'conditions': None
            })
        return self.save_keywords_advanced(cookie_id, keywords_advanced)

    def save_keywords_advanced(self, cookie_id: str, keywords: List[Dict[str, Any]]) -> bool:
        """保存关键字列表（支持所有新字段），先删除旧数据再插入新数据

        Args:
            cookie_id: 账号ID
            keywords: 关键词列表，每个关键词包含以下字段：
                - keyword: 关键词 (必填)
                - reply: 回复内容 (必填)
                - item_id: 商品ID (可选)
                - type: 类型 text/image (默认text)
                - image_url: 图片URL (可选)
                - match_type: 匹配类型 contains/exact/regex/prefix/suffix (默认contains)
                - priority: 优先级 0-100 (默认0)
                - reply_mode: 回复模式 single/random/sequential (默认single)
                - replies: 多回复列表JSON (可选)
                - conditions: 规则条件JSON (可选)

        Returns:
            bool: 保存是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "DELETE FROM keywords WHERE cookie_id = ?", (cookie_id,))

                for kw in keywords:
                    keyword = kw.get('keyword', '')
                    reply = kw.get('reply', '')
                    item_id = kw.get('item_id')
                    kw_type = kw.get('type', 'text')
                    image_url = kw.get('image_url')
                    match_type = normalize_match_type(kw.get('match_type', 'contains'))
                    priority = normalize_priority(kw.get('priority', 0))
                    reply_mode = kw.get('reply_mode', 'single')
                    replies = kw.get('replies')
                    conditions = kw.get('conditions')

                    normalized_item_id = item_id if item_id and str(item_id).strip() else None

                    try:
                        self._db._execute_sql(cursor,
                            """INSERT INTO keywords
                               (cookie_id, keyword, reply, item_id, type, image_url,
                                match_type, priority, reply_mode, replies, trigger_count, conditions, sequence_index)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 0)""",
                            (cookie_id, keyword, reply, normalized_item_id, kw_type, image_url,
                             match_type, priority, reply_mode, replies, conditions))
                    except sqlite3.IntegrityError as ie:
                        item_desc = f"商品ID: {normalized_item_id}" if normalized_item_id else "通用关键词"
                        logger.error(f"关键词唯一约束冲突: Cookie={cookie_id}, 关键词='{keyword}', {item_desc}")
                        raise ie

                self.conn.commit()
                logger.info(f"关键字保存成功: {cookie_id}, {len(keywords)}条")

                # 在锁内刷新缓存，确保数据一致性
                cache_success = self._refresh_matcher_cache_locked(cookie_id)
                if not cache_success:
                    logger.warning(f"关键字保存成功但缓存刷新失败: {cookie_id}")

            except Exception as e:
                logger.error(f"关键字保存失败: {e}")
                self.conn.rollback()
                return False

        return True

    def save_keywords_batch_with_transaction(self, keywords_data: List[Dict[str, Any]]) -> bool:
        """批量保存多个账号的关键词（使用事务）

        使用事务管理器确保批量操作的原子性，失败时自动回滚

        Args:
            keywords_data: 关键词数据列表，每个元素包含：
                - cookie_id: 账号ID
                - keywords: 关键词列表

        Returns:
            bool: 保存是否成功

        Example:
            keywords_data = [
                {
                    'cookie_id': 'account1',
                    'keywords': [
                        {'keyword': '你好', 'reply': '您好', 'match_type': 'contains'},
                        {'keyword': '价格', 'reply': '优惠中', 'match_type': 'exact'}
                    ]
                },
                {
                    'cookie_id': 'account2',
                    'keywords': [
                        {'keyword': '在吗', 'reply': '在的', 'match_type': 'contains'}
                    ]
                }
            ]
        """
        try:
            # 使用事务管理器
            with self._db.transaction:
                for data in keywords_data:
                    cookie_id = data.get('cookie_id')
                    keywords = data.get('keywords', [])

                    if not cookie_id:
                        logger.warning("批量保存关键词时缺少cookie_id")
                        continue

                    # 调用单个账号的保存方法（已在事务中，不会单独提交）
                    if not self.save_keywords_advanced(cookie_id, keywords):
                        raise Exception(f"保存关键词失败: {cookie_id}")

                    logger.debug(f"批量保存关键词: {cookie_id}, {len(keywords)}条")

                logger.info(f"批量保存关键词成功，共处理 {len(keywords_data)} 个账号")
                return True

        except Exception as e:
            logger.error(f"批量保存关键词失败，已回滚所有操作: {e}")
            return False

    def save_text_keywords_only(self, cookie_id: str, keywords: List[Tuple[str, str, str]]) -> bool:
        """保存文本关键字列表，只删除文本类型的关键词，保留图片关键词（向后兼容方法）"""
        # 转换为新格式
        keywords_advanced = []
        for keyword, reply, item_id in keywords:
            keywords_advanced.append({
                'keyword': keyword,
                'reply': reply,
                'item_id': item_id,
                'type': 'text',
                'match_type': 'contains',
                'priority': 0,
                'reply_mode': 'single',
                'replies': None,
                'conditions': None
            })
        return self.save_text_keywords_advanced(cookie_id, keywords_advanced)

    def save_text_keywords_advanced(self, cookie_id: str, keywords: List[Dict[str, Any]]) -> bool:
        """保存文本关键字列表（支持所有新字段），只删除文本类型的关键词，保留图片关键词

        Args:
            cookie_id: 账号ID
            keywords: 关键词列表，每个关键词包含以下字段：
                - keyword: 关键词 (必填)
                - reply: 回复内容 (必填)
                - item_id: 商品ID (可选)
                - match_type: 匹配类型 contains/exact/regex/prefix/suffix (默认contains)
                - priority: 优先级 0-100 (默认0)
                - reply_mode: 回复模式 single/random/sequential (默认single)
                - replies: 多回复列表JSON (可选)
                - conditions: 规则条件JSON (可选)

        Returns:
            bool: 保存是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor,
                    "DELETE FROM keywords WHERE cookie_id = ? AND (type IS NULL OR type = 'text')",
                    (cookie_id,))

                for kw in keywords:
                    keyword = kw.get('keyword', '')
                    reply = kw.get('reply', '')
                    item_id = kw.get('item_id')
                    match_type = normalize_match_type(kw.get('match_type', 'contains'))
                    priority = normalize_priority(kw.get('priority', 0))
                    reply_mode = kw.get('reply_mode', 'single')
                    replies = kw.get('replies')
                    conditions = kw.get('conditions')

                    normalized_item_id = item_id if item_id and str(item_id).strip() else None

                    try:
                        self._db._execute_sql(cursor,
                            """INSERT INTO keywords
                               (cookie_id, keyword, reply, item_id, type, match_type, priority, reply_mode, replies, trigger_count, conditions, sequence_index)
                               VALUES (?, ?, ?, ?, 'text', ?, ?, ?, ?, 0, ?, 0)""",
                            (cookie_id, keyword, reply, normalized_item_id, match_type, priority, reply_mode, replies, conditions))
                    except sqlite3.IntegrityError as ie:
                        item_desc = f"商品ID: {normalized_item_id}" if normalized_item_id else "通用关键词"
                        logger.error(f"关键词唯一约束冲突: Cookie={cookie_id}, 关键词='{keyword}', {item_desc}")
                        raise ie

                self.conn.commit()
                logger.info(f"文本关键字保存成功: {cookie_id}, {len(keywords)}条，图片关键词已保留")

                # 在锁内刷新缓存，确保数据一致性
                cache_success = self._refresh_matcher_cache_locked(cookie_id)
                if not cache_success:
                    logger.warning(f"文本关键字保存成功但缓存刷新失败: {cookie_id}")

            except Exception as e:
                logger.error(f"文本关键字保存失败: {e}")
                self.conn.rollback()
                return False

        return True

    def get_keywords(self, cookie_id: str) -> List[Tuple[str, str]]:
        """获取指定Cookie的关键字列表（向后兼容方法）"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "SELECT keyword, reply FROM keywords WHERE cookie_id = ?", (cookie_id,))
                return [(row[0], row[1]) for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"获取关键字失败: {e}")
                return []

    def get_keywords_with_item_id(self, cookie_id: str) -> List[Tuple[str, str, str]]:
        """获取指定Cookie的关键字列表（包含商品ID）"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor,
                    "SELECT keyword, reply, item_id FROM keywords WHERE cookie_id = ?",
                    (cookie_id,)
                )
                return [(row[0], row[1], row[2]) for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"获取关键字失败: {e}")
                return []

    def check_keyword_duplicate(self, cookie_id: str, keyword: str, item_id: str = None) -> bool:
        """检查关键词是否重复"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if item_id:
                    self._db._execute_sql(cursor,
                        "SELECT COUNT(*) FROM keywords WHERE cookie_id = ? AND keyword = ? AND item_id = ?",
                        (cookie_id, keyword, item_id))
                else:
                    self._db._execute_sql(cursor,
                        "SELECT COUNT(*) FROM keywords WHERE cookie_id = ? AND keyword = ? AND (item_id IS NULL OR item_id = '')",
                        (cookie_id, keyword))

                count = cursor.fetchone()[0]
                return count > 0
            except Exception as e:
                logger.error(f"检查关键词重复失败: {e}")
                return False

    def save_image_keyword(self, cookie_id: str, keyword: str, image_url: str, item_id: str = None) -> bool:
        """保存图片关键词（调用前应先检查重复）- 向后兼容方法"""
        return self.save_image_keyword_advanced(cookie_id, keyword, image_url, item_id)

    def save_image_keyword_advanced(self, cookie_id: str, keyword: str, image_url: str,
                                     item_id: str = None, match_type: str = 'contains',
                                     priority: int = 0, conditions: str = None) -> bool:
        """保存图片关键词（支持所有新字段）

        Args:
            cookie_id: 账号ID
            keyword: 关键词
            image_url: 图片URL
            item_id: 商品ID (可选)
            match_type: 匹配类型 contains/exact/regex/prefix/suffix (默认contains)
            priority: 优先级 0-100 (默认0)
            conditions: 规则条件JSON (可选)

        Returns:
            bool: 保存是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                normalized_item_id = item_id if item_id and item_id.strip() else None

                self._db._execute_sql(cursor,
                    """INSERT INTO keywords
                       (cookie_id, keyword, reply, item_id, type, image_url, match_type, priority, reply_mode, replies, trigger_count, conditions, sequence_index)
                       VALUES (?, ?, '', ?, 'image', ?, ?, ?, 'single', NULL, 0, ?, 0)""",
                    (cookie_id, keyword, normalized_item_id, image_url, match_type, priority, conditions))

                self.conn.commit()
                logger.info(f"图片关键词保存成功: {cookie_id}, 关键词: {keyword}, 图片: {image_url}")

                # 在锁内刷新缓存，确保数据一致性
                cache_success = self._refresh_matcher_cache_locked(cookie_id)
                if not cache_success:
                    logger.warning(f"图片关键词保存成功但缓存刷新失败: {cookie_id}")

            except Exception as e:
                logger.error(f"图片关键词保存失败: {e}")
                self.conn.rollback()
                return False

        return True

    def get_keywords_with_type(self, cookie_id: str) -> List[Dict[str, Any]]:
        """获取指定Cookie的关键字列表（包含类型信息和新字段）

        Args:
            cookie_id: 账号ID

        Returns:
            List[Dict[str, Any]]: 关键词列表，每个关键词包含以下字段：
                - keyword: 关键词
                - reply: 回复内容
                - item_id: 商品ID
                - type: 类型 (text/image)
                - image_url: 图片URL
                - match_type: 匹配类型 (contains/exact/regex/prefix/suffix)
                - priority: 优先级 (0-100)
                - reply_mode: 回复模式 (single/random/sequential)
                - replies: 多回复列表JSON
                - sequence_index: 顺序回复当前索引
                - trigger_count: 触发次数
                - conditions: 规则引擎条件JSON
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor,
                    """SELECT keyword, reply, item_id, type, image_url,
                              match_type, priority, reply_mode, replies,
                              sequence_index, trigger_count, conditions
                       FROM keywords WHERE cookie_id = ?""",
                    (cookie_id,)
                )

                results = []
                for row in cursor.fetchall():
                    keyword_data = {
                        'keyword': row[0],
                        'reply': row[1],
                        'item_id': row[2],
                        'type': row[3] or 'text',
                        'image_url': row[4],
                        'match_type': row[5] or 'contains',
                        'priority': row[6] if row[6] is not None else 0,
                        'reply_mode': row[7] or 'single',
                        'replies': row[8],
                        'sequence_index': row[9] if row[9] is not None else 0,
                        'trigger_count': row[10] if row[10] is not None else 0,
                        'conditions': row[11],
                    }
                    results.append(keyword_data)

                return results
            except Exception as e:
                logger.error(f"获取关键字失败: {e}")
                return []

    def update_keyword_image_url(self, cookie_id: str, keyword: str, new_image_url: str) -> bool:
        """更新关键词的图片URL"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor,
                    "UPDATE keywords SET image_url = ? WHERE cookie_id = ? AND keyword = ? AND type = 'image'",
                    (new_image_url, cookie_id, keyword)
                )

                if cursor.rowcount == 0:
                    logger.warning(f"未找到匹配的图片关键词: {cookie_id}, 关键词: {keyword}")
                    return False

                self.conn.commit()
                logger.info(f"关键词图片URL更新成功: {cookie_id}, 关键词: {keyword}, 新URL: {new_image_url}")

                # 在锁内刷新缓存，确保数据一致性
                cache_success = self._refresh_matcher_cache_locked(cookie_id)
                if not cache_success:
                    logger.warning(f"关键词图片URL更新成功但缓存刷新失败: {cookie_id}")

            except Exception as e:
                logger.error(f"更新关键词图片URL失败: {e}")
                self.conn.rollback()
                return False

        return True

    def delete_keyword_by_index(self, cookie_id: str, index: int) -> bool:
        """根据索引删除关键词"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor,
                    "SELECT id FROM keywords WHERE cookie_id = ? ORDER BY id",
                    (cookie_id,)
                )
                rows = cursor.fetchall()

                if 0 <= index < len(rows):
                    keyword_id = rows[index][0]
                    self._db._execute_sql(cursor, "DELETE FROM keywords WHERE id = ?", (keyword_id,))
                    self.conn.commit()
                    logger.info(f"删除关键词成功: {cookie_id}, 索引: {index}")

                    # 在锁内刷新缓存，确保数据一致性
                    cache_success = self._refresh_matcher_cache_locked(cookie_id)
                    if not cache_success:
                        logger.warning(f"删除关键词成功但缓存刷新失败: {cookie_id}")

                else:
                    logger.warning(f"关键词索引超出范围: {index}")
                    return False

            except Exception as e:
                logger.error(f"删除关键词失败: {e}")
                self.conn.rollback()
                return False

        return True

    def get_all_keywords(self, user_id: int = None) -> Dict[str, List[Tuple[str, str]]]:
        """获取所有Cookie的关键字（支持用户隔离）"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if user_id is not None:
                    cursor.execute("""
                    SELECT k.cookie_id, k.keyword, k.reply
                    FROM keywords k
                    JOIN cookies c ON k.cookie_id = c.id
                    WHERE c.user_id = ?
                    """, (user_id,))
                else:
                    self._db._execute_sql(cursor, "SELECT cookie_id, keyword, reply FROM keywords")

                result = {}
                for row in cursor.fetchall():
                    cookie_id, keyword, reply = row
                    if cookie_id not in result:
                        result[cookie_id] = []
                    result[cookie_id].append((keyword, reply))

                return result
            except Exception as e:
                logger.error(f"获取所有关键字失败: {e}")
                return {}

    def increment_trigger_count(self, cookie_id: str, keyword: str, item_id: str = None) -> bool:
        """增加关键词触发次数

        Args:
            cookie_id: 账号ID
            keyword: 关键词
            item_id: 商品ID (可选)

        Returns:
            bool: 更新是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if item_id:
                    self._db._execute_sql(cursor,
                        "UPDATE keywords SET trigger_count = trigger_count + 1 WHERE cookie_id = ? AND keyword = ? AND item_id = ?",
                        (cookie_id, keyword, item_id))
                else:
                    self._db._execute_sql(cursor,
                        "UPDATE keywords SET trigger_count = trigger_count + 1 WHERE cookie_id = ? AND keyword = ? AND (item_id IS NULL OR item_id = '')",
                        (cookie_id, keyword))

                self.conn.commit()
                logger.debug(f"关键词触发次数+1: {cookie_id}, 关键词: {keyword}")
                return True
            except Exception as e:
                logger.error(f"更新关键词触发次数失败: {e}")
                self.conn.rollback()
                return False

    def update_keyword_advanced(self, cookie_id: str, keyword: str, item_id: str = None,
                                match_type: str = None, priority: int = None,
                                reply_mode: str = None, replies: str = None,
                                conditions: str = None, reply: str = None) -> bool:
        """更新关键词的高级字段

        Args:
            cookie_id: 账号ID
            keyword: 关键词
            item_id: 商品ID (可选)
            match_type: 匹配类型 (可选)
            priority: 优先级 (可选)
            reply_mode: 回复模式 (可选)
            replies: 多回复列表JSON (可选)
            conditions: 规则条件JSON (可选)
            reply: 回复内容 (可选)

        Returns:
            bool: 更新是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # 构建动态更新语句
                updates = []
                params = []

                if match_type is not None:
                    updates.append("match_type = ?")
                    params.append(match_type)
                if priority is not None:
                    updates.append("priority = ?")
                    params.append(priority)
                if reply_mode is not None:
                    updates.append("reply_mode = ?")
                    params.append(reply_mode)
                if replies is not None:
                    updates.append("replies = ?")
                    params.append(replies)
                if conditions is not None:
                    updates.append("conditions = ?")
                    params.append(conditions)
                if reply is not None:
                    updates.append("reply = ?")
                    params.append(reply)

                if not updates:
                    logger.warning("没有需要更新的字段")
                    return False

                # 添加WHERE条件参数
                params.extend([cookie_id, keyword])
                where_clause = "cookie_id = ? AND keyword = ?"
                if item_id:
                    params.append(item_id)
                    where_clause += " AND item_id = ?"
                else:
                    where_clause += " AND (item_id IS NULL OR item_id = '')"

                sql = f"UPDATE keywords SET {', '.join(updates)} WHERE {where_clause}"
                self._db._execute_sql(cursor, sql, params)

                if cursor.rowcount == 0:
                    logger.warning(f"未找到匹配的关键词: {cookie_id}, 关键词: {keyword}")
                    return False

                self.conn.commit()
                logger.info(f"关键词更新成功: {cookie_id}, 关键词: {keyword}")

                # 在锁内刷新缓存
                cache_success = self._refresh_matcher_cache_locked(cookie_id)
                if not cache_success:
                    logger.warning(f"关键词更新成功但缓存刷新失败: {cookie_id}")

                return True
            except Exception as e:
                logger.error(f"更新关键词失败: {e}")
                self.conn.rollback()
                return False

    def get_keywords_by_priority(self, cookie_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """按优先级获取关键词列表

        Args:
            cookie_id: 账号ID
            limit: 返回数量限制 (可选)

        Returns:
            List[Dict[str, Any]]: 按优先级排序的关键词列表
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                sql = """
                    SELECT keyword, reply, item_id, type, image_url,
                           match_type, priority, reply_mode, replies, trigger_count, conditions
                    FROM keywords
                    WHERE cookie_id = ?
                    ORDER BY priority DESC, trigger_count ASC
                """
                if limit:
                    sql += f" LIMIT {limit}"

                self._db._execute_sql(cursor, sql, (cookie_id,))

                results = []
                for row in cursor.fetchall():
                    keyword_data = {
                        'keyword': row[0],
                        'reply': row[1],
                        'item_id': row[2],
                        'type': row[3] or 'text',
                        'image_url': row[4],
                        'match_type': row[5] or 'contains',
                        'priority': row[6] or 0,
                        'reply_mode': row[7] or 'single',
                        'replies': row[8],
                        'trigger_count': row[9] or 0,
                        'conditions': row[10]
                    }
                    results.append(keyword_data)

                return results
            except Exception as e:
                logger.error(f"按优先级获取关键词失败: {e}")
                return []

    def get_keyword_stats(self, cookie_id: str) -> Dict[str, Any]:
        """获取关键词统计信息

        Args:
            cookie_id: 账号ID

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # 总数
                self._db._execute_sql(cursor,
                    "SELECT COUNT(*) FROM keywords WHERE cookie_id = ?", (cookie_id,))
                total_count = cursor.fetchone()[0]

                # 按类型统计
                self._db._execute_sql(cursor,
                    "SELECT type, COUNT(*) FROM keywords WHERE cookie_id = ? GROUP BY type",
                    (cookie_id,))
                type_stats = {row[0] or 'text': row[1] for row in cursor.fetchall()}

                # 按匹配类型统计
                self._db._execute_sql(cursor,
                    "SELECT match_type, COUNT(*) FROM keywords WHERE cookie_id = ? GROUP BY match_type",
                    (cookie_id,))
                match_type_stats = {row[0] or 'contains': row[1] for row in cursor.fetchall()}

                # 总触发次数
                self._db._execute_sql(cursor,
                    "SELECT SUM(trigger_count) FROM keywords WHERE cookie_id = ?", (cookie_id,))
                total_triggers = cursor.fetchone()[0] or 0

                return {
                    'total_count': total_count,
                    'type_stats': type_stats,
                    'match_type_stats': match_type_stats,
                    'total_triggers': total_triggers
                }
            except Exception as e:
                logger.error(f"获取关键词统计信息失败: {e}")
                return {
                    'total_count': 0,
                    'type_stats': {},
                    'match_type_stats': {},
                    'total_triggers': 0
                }

    def update_sequence_index(
        self,
        cookie_id: str,
        keyword: str,
        item_id: Optional[str],
        new_index: int
    ) -> bool:
        """更新顺序回复的当前索引

        Args:
            cookie_id: 账号ID
            keyword: 关键词
            item_id: 商品ID（可为None）
            new_index: 新的索引值

        Returns:
            bool: 更新是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()

                if item_id:
                    self._db._execute_sql(cursor,
                        "UPDATE keywords SET sequence_index = ? WHERE cookie_id = ? AND keyword = ? AND item_id = ?",
                        (new_index, cookie_id, keyword, item_id))
                else:
                    self._db._execute_sql(cursor,
                        "UPDATE keywords SET sequence_index = ? WHERE cookie_id = ? AND keyword = ? AND (item_id IS NULL OR item_id = '')",
                        (new_index, cookie_id, keyword))

                if cursor.rowcount == 0:
                    logger.warning(f"未找到匹配的关键词: cookie_id={cookie_id}, keyword={keyword}, item_id={item_id}")
                    return False

                self.conn.commit()
                logger.debug(f"顺序回复索引更新成功: cookie_id={cookie_id}, keyword={keyword}, new_index={new_index}")
                return True

            except Exception as e:
                logger.error(f"更新顺序回复索引失败: {e}")
                self.conn.rollback()
                return False

    def get_sequence_index(
        self,
        cookie_id: str,
        keyword: str,
        item_id: Optional[str]
    ) -> int:
        """获取顺序回复的当前索引

        Args:
            cookie_id: 账号ID
            keyword: 关键词
            item_id: 商品ID（可为None）

        Returns:
            int: 当前索引值，默认为0
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()

                if item_id:
                    self._db._execute_sql(cursor,
                        "SELECT sequence_index FROM keywords WHERE cookie_id = ? AND keyword = ? AND item_id = ?",
                        (cookie_id, keyword, item_id))
                else:
                    self._db._execute_sql(cursor,
                        "SELECT sequence_index FROM keywords WHERE cookie_id = ? AND keyword = ? AND (item_id IS NULL OR item_id = '')",
                        (cookie_id, keyword))

                row = cursor.fetchone()
                if row:
                    return row[0] if row[0] is not None else 0
                return 0

            except Exception as e:
                logger.error(f"获取顺序回复索引失败: {e}")
                return 0
