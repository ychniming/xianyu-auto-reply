"""
闲鱼自动回复系统 - 商品数据库模块
负责商品信息的数据库操作
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger

from app.services.xianyu.common import safe_str


class ItemDBManager:
    """商品数据库管理器"""

    def __init__(self, parent):
        self.parent = parent

    def _safe_str(self, obj) -> str:
        """安全转换为字符串"""
        return safe_str(obj)

    async def save_item_info_to_db(self, item_id: str, item_detail: str = None, item_title: str = None) -> None:
        """保存商品信息到数据库

        Args:
            item_id: 商品ID
            item_detail: 商品详情
            item_title: 商品标题
        """
        try:
            if item_id and item_id.startswith('auto_'):
                logger.debug(f"跳过保存自动生成的商品ID: {item_id}")
                return

            if not item_title and not item_detail:
                logger.debug(f"跳过保存商品信息：缺少商品标题和详情 - {item_id}")
                return

            if not item_title or not item_detail:
                logger.debug(f"跳过保存商品信息：商品标题或详情不完整 - {item_id}")
                return

            from app.repositories import db_manager
            item_data = item_detail
            success = db_manager.save_item_info(self.parent.cookie_id, item_id, item_data)
            if success:
                logger.info(f"商品信息已保存到数据库: {item_id}")
            else:
                logger.warning(f"保存商品信息到数据库失败: {item_id}")

        except Exception as e:
            logger.error(f"保存商品信息到数据库异常: {self._safe_str(e)}")

    async def save_item_detail_only(self, item_id: str, item_detail: str) -> bool:
        """仅保存商品详情

        Args:
            item_id: 商品ID
            item_detail: 商品详情

        Returns:
            bool: 保存是否成功
        """
        try:
            from app.repositories import db_manager
            success = db_manager.update_item_detail(self.parent.cookie_id, item_id, item_detail)
            if success:
                logger.info(f"商品详情已更新: {item_id}")
            else:
                logger.warning(f"更新商品详情失败: {item_id}")
            return success
        except Exception as e:
            logger.error(f"更新商品详情异常: {self._safe_str(e)}")
            return False

    async def fetch_item_detail_from_api(self, item_id: str) -> str:
        """从外部API获取商品详情

        Args:
            item_id: 商品ID

        Returns:
            str: 商品详情文本
        """
        try:
            from configs.config import config

            auto_fetch_config = config.get('ITEM_DETAIL', {}).get('auto_fetch', {})

            if not auto_fetch_config.get('enabled', True):
                logger.debug(f"自动获取商品详情功能已禁用: {item_id}")
                return ""

            api_base_url = auto_fetch_config.get('api_url', 'https://selfapi.zhinianboke.com/api/getItemDetail')
            timeout_seconds = auto_fetch_config.get('timeout', 10)
            api_url = f"{api_base_url}/{item_id}"

            logger.info(f"正在从外部API获取商品详情: {item_id}")
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('status') == '200' and result.get('data'):
                            item_detail = result['data']
                            logger.info(f"成功获取商品详情: {item_id}, 长度: {len(item_detail)}")
                            return item_detail
                        else:
                            logger.warning(f"API返回状态异常: {result.get('status')}, message: {result.get('message')}")
                            return ""
                    else:
                        logger.warning(f"API请求失败: HTTP {response.status}")
                        return ""

        except asyncio.TimeoutError:
            logger.warning(f"获取商品详情超时: {item_id}")
            return ""
        except Exception as e:
            logger.error(f"获取商品详情异常: {item_id}, 错误: {self._safe_str(e)}")
            return ""

    async def save_items_list_to_db(self, items_list: List[Dict[str, Any]]) -> int:
        """批量保存商品列表信息到数据库

        Args:
            items_list: 商品列表

        Returns:
            int: 保存成功的数量
        """
        try:
            from app.repositories import db_manager
            from configs.config import config

            batch_data = []
            items_need_detail = []

            for item in items_list:
                item_id = item.get('id')
                if not item_id or item_id.startswith('auto_'):
                    continue

                item_detail = {
                    'title': item.get('title', ''),
                    'price': item.get('price', ''),
                    'price_text': item.get('price_text', ''),
                    'category_id': item.get('category_id', ''),
                    'auction_type': item.get('auction_type', ''),
                    'item_status': item.get('item_status', 0),
                    'detail_url': item.get('detail_url', ''),
                    'pic_info': item.get('pic_info', {}),
                    'detail_params': item.get('detail_params', {}),
                    'track_params': item.get('track_params', {}),
                    'item_label_data': item.get('item_label_data', {}),
                    'card_type': item.get('card_type', 0)
                }

                existing_item = db_manager.get_item_info(self.parent.cookie_id, item_id)
                has_detail = existing_item and existing_item.get('item_detail') and existing_item['item_detail'].strip()

                batch_data.append({
                    'cookie_id': self.parent.cookie_id,
                    'item_id': item_id,
                    'item_title': item.get('title', ''),
                    'item_description': '',
                    'item_category': str(item.get('category_id', '')),
                    'item_price': item.get('price_text', ''),
                    'item_detail': json.dumps(item_detail, ensure_ascii=False)
                })

                if not has_detail:
                    items_need_detail.append({
                        'item_id': item_id,
                        'item_title': item.get('title', '')
                    })

            if not batch_data:
                logger.info("没有有效的商品数据需要保存")
                return 0

            saved_count = db_manager.batch_save_item_basic_info(batch_data)
            logger.info(f"批量保存商品信息完成: {saved_count}/{len(batch_data)} 个商品")

            if items_need_detail:
                auto_fetch_config = config.get('ITEM_DETAIL', {}).get('auto_fetch', {})

                if auto_fetch_config.get('enabled', True):
                    logger.info(f"发现 {len(items_need_detail)} 个商品缺少详情，开始获取...")
                    detail_success_count = await self._fetch_missing_item_details(items_need_detail)
                    logger.info(f"成功获取 {detail_success_count}/{len(items_need_detail)} 个商品的详情")

            return saved_count

        except Exception as e:
            logger.error(f"批量保存商品信息异常: {safe_str(e)}")
            return 0

    async def _fetch_missing_item_details(self, items_need_detail: List[Dict[str, str]]) -> int:
        """批量获取缺失的商品详情

        Args:
            items_need_detail: 需要获取详情的商品列表

        Returns:
            int: 成功获取的数量
        """
        success_count = 0
        try:
            from configs.config import config

            auto_fetch_config = config.get('ITEM_DETAIL', {}).get('auto_fetch', {})
            max_concurrent = auto_fetch_config.get('max_concurrent', 3)
            retry_delay = auto_fetch_config.get('retry_delay', 0.5)

            semaphore = asyncio.Semaphore(max_concurrent)

            async def fetch_single_item_detail(item_info: Dict[str, str]) -> int:
                async with semaphore:
                    try:
                        item_id = item_info['item_id']
                        item_title = item_info['item_title']
                        item_detail_text = await self.fetch_item_detail_from_api(item_id)

                        if item_detail_text:
                            success = await self.save_item_detail_only(item_id, item_detail_text)
                            if success:
                                logger.info(f"✅ 成功获取并保存商品详情: {item_id} - {item_title}")
                                return 1
                            else:
                                logger.warning(f"❌ 获取详情成功但保存失败: {item_id}")
                        else:
                            logger.warning(f"❌ 未能获取商品详情: {item_id} - {item_title}")

                        await asyncio.sleep(retry_delay)
                        return 0

                    except Exception as e:
                        logger.error(f"获取单个商品详情异常: {item_info.get('item_id', 'unknown')}, 错误: {safe_str(e)}")
                        return 0

            tasks = [fetch_single_item_detail(item_info) for item_info in items_need_detail]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, int):
                    success_count += result
                elif isinstance(result, Exception):
                    logger.error(f"获取商品详情任务异常: {result}")

            return success_count

        except Exception as e:
            logger.error(f"批量获取商品详情异常: {safe_str(e)}")
            return success_count
