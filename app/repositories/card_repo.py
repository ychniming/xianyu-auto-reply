"""卡券和发货规则仓储模块

提供卡券、发货规则等数据的操作
"""
import json
from typing import List, Dict, Optional, Any
from loguru import logger

from .card_helpers import (
    _build_card_from_row,
    _build_rule_from_row,
    _build_rule_with_spec_from_row,
    _build_rule_with_spec_name_from_row
)


class CardRepository:
    """卡券数据访问层"""

    def __init__(self, db_manager):
        """初始化仓储

        Args:
            db_manager: DBManager实例引用
        """
        self._db = db_manager
        self.conn = db_manager.conn
        self.lock = db_manager.lock

    # -------------------- 卡券管理 --------------------
    def create_card(self, name: str, card_type: str, api_config: Dict[str, Any] = None,
                   text_content: str = None, data_content: str = None,
                   image_url: str = None, description: str = None,
                   delay_seconds: int = 0, is_multi_spec: bool = False,
                   spec_name: str = None, spec_value: str = None,
                   user_id: int = None) -> int:
        """创建卡券

        Args:
            name: 卡券名称
            card_type: 卡券类型
            api_config: API配置字典
            text_content: 文本内容
            data_content: 数据内容
            image_url: 图片URL
            description: 描述
            delay_seconds: 延迟秒数
            is_multi_spec: 是否多规格
            spec_name: 规格名称
            spec_value: 规格值
            user_id: 用户ID

        Returns:
            int: 新创建的卡券ID
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if api_config is None:
                    api_config = {}
                api_config_str = json.dumps(api_config) if isinstance(api_config, dict) else api_config

                cursor.execute('''
                INSERT INTO cards (name, type, api_config, text_content, data_content,
                                  image_url, description, delay_seconds, is_multi_spec,
                                  spec_name, spec_value, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, card_type, api_config_str, text_content, data_content,
                      image_url, description, delay_seconds, is_multi_spec,
                      spec_name, spec_value, user_id))
                self.conn.commit()
                card_id = cursor.lastrowid
                logger.debug(f"创建卡券: {name} (ID: {card_id})")
                return card_id
            except Exception as e:
                logger.error(f"创建卡券失败: {e}")
                self.conn.rollback()
                raise

    def get_all_cards(self, user_id: int = None) -> List[Dict[str, Any]]:
        """获取所有卡券

        Args:
            user_id: 用户ID筛选，不传则返回所有

        Returns:
            List[Dict[str, Any]]: 卡券列表
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if user_id is not None:
                    cursor.execute('''
                    SELECT id, name, type, api_config, text_content, data_content,
                           image_url, description, enabled, delay_seconds,
                           is_multi_spec, spec_name, spec_value, user_id,
                           created_at, updated_at
                    FROM cards WHERE user_id = ? ORDER BY created_at DESC
                    ''', (user_id,))
                else:
                    cursor.execute('''
                    SELECT id, name, type, api_config, text_content, data_content,
                           image_url, description, enabled, delay_seconds,
                           is_multi_spec, spec_name, spec_value, user_id,
                           created_at, updated_at
                    FROM cards ORDER BY created_at DESC
                    ''')

                cards = []
                for row in cursor.fetchall():
                    cards.append(_build_card_from_row(row))
                return cards
            except Exception as e:
                logger.error(f"获取所有卡券失败: {e}")
                return []

    def get_card_by_id(self, card_id: int, user_id: int = None) -> Optional[Dict[str, Any]]:
        """根据ID获取卡券

        Args:
            card_id: 卡券ID
            user_id: 用户ID筛选，不传则不限制

        Returns:
            Optional[Dict[str, Any]]: 卡券信息，未找到返回None
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if user_id is not None:
                    cursor.execute('''
                    SELECT id, name, type, api_config, text_content, data_content,
                           image_url, description, enabled, delay_seconds,
                           is_multi_spec, spec_name, spec_value, user_id,
                           created_at, updated_at
                    FROM cards WHERE id = ? AND user_id = ?
                    ''', (card_id, user_id))
                else:
                    cursor.execute('''
                    SELECT id, name, type, api_config, text_content, data_content,
                           image_url, description, enabled, delay_seconds,
                           is_multi_spec, spec_name, spec_value, user_id,
                           created_at, updated_at
                    FROM cards WHERE id = ?
                    ''', (card_id,))

                row = cursor.fetchone()
                if row:
                    return _build_card_from_row(row)
                return None
            except Exception as e:
                logger.error(f"获取卡券失败: {e}")
                return None

    def update_card(self, card_id: int, name: str = None, card_type: str = None,
                   api_config: Dict[str, Any] = None, text_content: str = None,
                   data_content: str = None, image_url: str = None,
                   description: str = None, enabled: bool = None,
                   delay_seconds: int = None, is_multi_spec: bool = None,
                   spec_name: str = None, spec_value: str = None,
                   user_id: int = None) -> bool:
        """更新卡券

        Args:
            card_id: 卡券ID
            name: 卡券名称
            card_type: 卡券类型
            api_config: API配置字典
            text_content: 文本内容
            data_content: 数据内容
            image_url: 图片URL
            description: 描述
            enabled: 是否启用
            delay_seconds: 延迟秒数
            is_multi_spec: 是否多规格
            spec_name: 规格名称
            spec_value: 规格值
            user_id: 用户ID筛选，不传则不限制

        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # 构建更新语句
                updates = []
                params = []

                if name is not None:
                    updates.append("name = ?")
                    params.append(name)
                if card_type is not None:
                    updates.append("type = ?")
                    params.append(card_type)
                if api_config is not None:
                    updates.append("api_config = ?")
                    params.append(json.dumps(api_config) if isinstance(api_config, dict) else api_config)
                if text_content is not None:
                    updates.append("text_content = ?")
                    params.append(text_content)
                if data_content is not None:
                    updates.append("data_content = ?")
                    params.append(data_content)
                if image_url is not None:
                    updates.append("image_url = ?")
                    params.append(image_url)
                if description is not None:
                    updates.append("description = ?")
                    params.append(description)
                if enabled is not None:
                    updates.append("enabled = ?")
                    params.append(enabled)
                if delay_seconds is not None:
                    updates.append("delay_seconds = ?")
                    params.append(delay_seconds)
                if is_multi_spec is not None:
                    updates.append("is_multi_spec = ?")
                    params.append(is_multi_spec)
                if spec_name is not None:
                    updates.append("spec_name = ?")
                    params.append(spec_name)
                if spec_value is not None:
                    updates.append("spec_value = ?")
                    params.append(spec_value)

                if not updates:
                    return True

                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(card_id)
                if user_id is not None:
                    params.append(user_id)

                sql = f"UPDATE cards SET {', '.join(updates)} WHERE id = ?"
                if user_id is not None:
                    sql += " AND user_id = ?"

                cursor.execute(sql, params)
                self.conn.commit()
                logger.debug(f"更新卡券: {card_id}")
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"更新卡券失败: {e}")
                self.conn.rollback()
                return False

    def update_card_image_url(self, card_id: int, new_image_url: str) -> bool:
        """更新卡券图片URL

        Args:
            card_id: 卡券ID
            new_image_url: 新的图片URL

        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                UPDATE cards SET image_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (new_image_url, card_id))
                self.conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"更新卡券图片URL失败: {e}")
                self.conn.rollback()
                return False

    def delete_card(self, card_id: int) -> bool:
        """删除卡券

        Args:
            card_id: 卡券ID

        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "DELETE FROM cards WHERE id = ?", (card_id,))
                self.conn.commit()
                logger.debug(f"删除卡券: {card_id}")
                return True
            except Exception as e:
                logger.error(f"删除卡券失败: {e}")
                self.conn.rollback()
                return False

    def save_cards_batch_with_transaction(self, cards_data: List[Dict[str, Any]], user_id: int = None) -> bool:
        """批量保存卡券（使用事务）

        使用事务管理器确保批量操作的原子性，失败时自动回滚

        Args:
            cards_data: 卡券数据列表
            user_id: 用户ID

        Returns:
            bool: 保存是否成功

        Example:
            cards_data = [
                {
                    'name': '卡券1',
                    'type': 'text',
                    'text_content': '这是卡券内容',
                    'description': '描述'
                },
                {
                    'name': '卡券2',
                    'type': 'api',
                    'api_config': {'url': 'http://example.com'},
                    'description': 'API卡券'
                }
            ]
        """
        try:
            # 使用事务管理器
            with self._db.transaction:
                for card_data in cards_data:
                    card_id = self.create_card(
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

                    logger.debug(f"批量保存卡券: {card_data.get('name')} (ID: {card_id})")

                logger.info(f"批量保存卡券成功，共处理 {len(cards_data)} 张卡券")
                return True

        except Exception as e:
            logger.error(f"批量保存卡券失败，已回滚所有操作: {e}")
            return False

    def consume_batch_data(self, card_id: int) -> Optional[Dict[str, Any]]:
        """消费卡券的批次数据

        Args:
            card_id: 卡券ID

        Returns:
            Optional[Dict[str, Any]]: 批次数据，耗尽或失败返回None
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT id, data_content FROM cards WHERE id = ? AND type = 'data' AND enabled = 1
                ''', (card_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                data_content = row[1]
                if not data_content:
                    return None

                try:
                    data_list = json.loads(data_content)
                    if not data_list:
                        return None

                    # 返回第一条数据
                    data = data_list[0]
                    remaining = data_list[1:]

                    # 更新卡券数据
                    cursor.execute('''
                    UPDATE cards SET data_content = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''', (json.dumps(remaining), card_id))
                    self.conn.commit()

                    return data
                except json.JSONDecodeError:
                    logger.error(f"解析卡券批次数据失败: {card_id}")
                    return None
            except Exception as e:
                logger.error(f"消费卡券批次数据失败: {e}")
                return None

    # -------------------- 发货规则管理 --------------------
    def create_delivery_rule(self, keyword: str, card_id: int, delivery_count: int = 1,
                            enabled: bool = True, description: str = None,
                            user_id: int = None) -> int:
        """创建发货规则

        Args:
            keyword: 关键词
            card_id: 关联的卡券ID
            delivery_count: 发货次数
            enabled: 是否启用
            description: 描述
            user_id: 用户ID

        Returns:
            int: 新创建的发货规则ID
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT INTO delivery_rules (keyword, card_id, delivery_count, enabled, description)
                VALUES (?, ?, ?, ?, ?)
                ''', (keyword, card_id, delivery_count, enabled, description))
                self.conn.commit()
                rule_id = cursor.lastrowid
                logger.debug(f"创建发货规则: {keyword} -> {card_id} (ID: {rule_id})")
                return rule_id
            except Exception as e:
                logger.error(f"创建发货规则失败: {e}")
                self.conn.rollback()
                raise

    def get_all_delivery_rules(self, user_id: int = None) -> List[Dict[str, Any]]:
        """获取所有发货规则

        Args:
            user_id: 用户ID筛选，不传则返回所有

        Returns:
            List[Dict[str, Any]]: 发货规则列表
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if user_id is not None:
                    cursor.execute('''
                    SELECT dr.id, dr.keyword, dr.card_id, dr.delivery_count, dr.enabled,
                           dr.description, dr.delivery_times, dr.user_id,
                           c.name as card_name, c.type as card_type
                    FROM delivery_rules dr
                    LEFT JOIN cards c ON dr.card_id = c.id
                    WHERE dr.user_id = ?
                    ORDER BY dr.created_at DESC
                    ''', (user_id,))
                else:
                    cursor.execute('''
                    SELECT dr.id, dr.keyword, dr.card_id, dr.delivery_count, dr.enabled,
                           dr.description, dr.delivery_times, dr.user_id,
                           c.name as card_name, c.type as card_type
                    FROM delivery_rules dr
                    LEFT JOIN cards c ON dr.card_id = c.id
                    ORDER BY dr.created_at DESC
                    ''')

                rules = []
                for row in cursor.fetchall():
                    rules.append(_build_rule_from_row(row))
                return rules
            except Exception as e:
                logger.error(f"获取所有发货规则失败: {e}")
                return []

    def get_delivery_rules_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """根据关键词获取发货规则（模糊匹配）

        使用模糊匹配：商品标题包含关键词时触发发货。
        按关键词长度降序排序，确保更精确的关键词优先匹配。

        Args:
            keyword: 商品标题或关键词

        Returns:
            List[Dict[str, Any]]: 匹配的发货规则列表，包含卡券详细信息
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT dr.id, dr.keyword, dr.card_id, dr.delivery_count, dr.enabled,
                       dr.description, dr.delivery_times,
                       c.name as card_name, c.type as card_type,
                       c.delay_seconds as card_delay_seconds, c.description as card_description,
                       c.is_multi_spec, c.spec_name, c.spec_value
                FROM delivery_rules dr
                LEFT JOIN cards c ON dr.card_id = c.id
                WHERE ? LIKE '%' || dr.keyword || '%' AND dr.enabled = 1
                ORDER BY LENGTH(dr.keyword) DESC
                ''', (keyword,))

                rules = []
                for row in cursor.fetchall():
                    rules.append(_build_rule_with_spec_from_row(row))
                return rules
            except Exception as e:
                logger.error(f"获取发货规则失败: {e}")
                return []

    def get_delivery_rule_by_id(self, rule_id: int, user_id: int = None) -> Optional[Dict[str, Any]]:
        """根据ID获取发货规则

        Args:
            rule_id: 发货规则ID
            user_id: 用户ID筛选，不传则不限制

        Returns:
            Optional[Dict[str, Any]]: 发货规则信息，未找到返回None
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if user_id is not None:
                    cursor.execute('''
                    SELECT dr.id, dr.keyword, dr.card_id, dr.delivery_count, dr.enabled,
                           dr.description, dr.delivery_times, dr.user_id,
                           c.name as card_name, c.type as card_type
                    FROM delivery_rules dr
                    LEFT JOIN cards c ON dr.card_id = c.id
                    WHERE dr.id = ? AND dr.user_id = ?
                    ''', (rule_id, user_id))
                else:
                    cursor.execute('''
                    SELECT dr.id, dr.keyword, dr.card_id, dr.delivery_count, dr.enabled,
                           dr.description, dr.delivery_times, dr.user_id,
                           c.name as card_name, c.type as card_type
                    FROM delivery_rules dr
                    LEFT JOIN cards c ON dr.card_id = c.id
                    WHERE dr.id = ?
                    ''', (rule_id,))

                row = cursor.fetchone()
                if row:
                    return _build_rule_from_row(row)
                return None
            except Exception as e:
                logger.error(f"获取发货规则失败: {e}")
                return None

    def update_delivery_rule(self, rule_id: int, keyword: str = None, card_id: int = None,
                            delivery_count: int = None, enabled: bool = None,
                            description: str = None, user_id: int = None) -> bool:
        """更新发货规则

        Args:
            rule_id: 发货规则ID
            keyword: 关键词
            card_id: 关联的卡券ID
            delivery_count: 发货次数
            enabled: 是否启用
            description: 描述
            user_id: 用户ID筛选，不传则不限制

        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                updates = []
                params = []

                if keyword is not None:
                    updates.append("keyword = ?")
                    params.append(keyword)
                if card_id is not None:
                    updates.append("card_id = ?")
                    params.append(card_id)
                if delivery_count is not None:
                    updates.append("delivery_count = ?")
                    params.append(delivery_count)
                if enabled is not None:
                    updates.append("enabled = ?")
                    params.append(enabled)
                if description is not None:
                    updates.append("description = ?")
                    params.append(description)

                if not updates:
                    return True

                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(rule_id)
                if user_id is not None:
                    params.append(user_id)

                sql = f"UPDATE delivery_rules SET {', '.join(updates)} WHERE id = ?"
                if user_id is not None:
                    sql += " AND user_id = ?"

                cursor.execute(sql, params)
                self.conn.commit()
                logger.debug(f"更新发货规则: {rule_id}")
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"更新发货规则失败: {e}")
                self.conn.rollback()
                return False

    def increment_delivery_times(self, rule_id: int) -> None:
        """增加发货次数

        Args:
            rule_id: 发货规则ID
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                UPDATE delivery_rules SET delivery_times = delivery_times + 1
                WHERE id = ?
                ''', (rule_id,))
                self.conn.commit()
            except Exception as e:
                logger.error(f"增加发货次数失败: {e}")

    def get_delivery_rules_by_keyword_and_spec(self, keyword: str, spec_name: str = None,
                                               spec_value: str = None) -> List[Dict[str, Any]]:
        """根据关键词和规格获取发货规则

        Args:
            keyword: 关键词
            spec_name: 规格名称
            spec_value: 规格值

        Returns:
            List[Dict[str, Any]]: 匹配的发货规则列表
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()

                if spec_name and spec_value:
                    # 先尝试精确匹配
                    cursor.execute('''
                    SELECT dr.id, dr.keyword, dr.card_id, dr.delivery_count, dr.enabled,
                           dr.description, dr.delivery_times, dr.user_id,
                           c.name as card_name, c.type as card_type,
                           c.spec_name, c.spec_value
                    FROM delivery_rules dr
                    LEFT JOIN cards c ON dr.card_id = c.id
                    WHERE dr.keyword = ? AND dr.enabled = 1
                    ''', (keyword,))

                    rules = []
                    for row in cursor.fetchall():
                        card_spec_name = row[10]
                        card_spec_value = row[11]

                        # 优先匹配规格完全一致的规则
                        if card_spec_name == spec_name and card_spec_value == spec_value:
                            rules.insert(0, _build_rule_with_spec_name_from_row(row))
                        else:
                            rules.append(_build_rule_with_spec_name_from_row(row))

                    return rules
                else:
                    return self.get_delivery_rules_by_keyword(keyword)
            except Exception as e:
                logger.error(f"获取发货规则失败: {e}")
                return []

    def delete_delivery_rule(self, rule_id: int, user_id: int = None) -> bool:
        """删除发货规则

        Args:
            rule_id: 发货规则ID
            user_id: 用户ID筛选，不传则不限制

        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            try:
                cursor = self.conn.cursor()
                if user_id is not None:
                    self._db._execute_sql(cursor,
                        "DELETE FROM delivery_rules WHERE id = ? AND user_id = ?",
                        (rule_id, user_id)
                    )
                else:
                    self._db._execute_sql(cursor,
                        "DELETE FROM delivery_rules WHERE id = ?",
                        (rule_id,)
                    )
                self.conn.commit()
                logger.debug(f"删除发货规则: {rule_id}")
                return True
            except Exception as e:
                logger.error(f"删除发货规则失败: {e}")
                self.conn.rollback()
                return False
