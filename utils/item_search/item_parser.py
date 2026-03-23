"""
闲鱼商品搜索模块 - 数据解析器
负责商品数据解析、提取和转换
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger


class ItemDataParser:
    """商品数据解析器 - 负责解析和转换商品数据"""

    @staticmethod
    async def safe_get(data: Dict, *keys, default: Any = "暂无") -> Any:
        """安全获取嵌套字典值

        Args:
            data: 数据字典
            *keys: 键路径
            default: 默认值

        Returns:
            Any: 获取到的值或默认值
        """
        for key in keys:
            try:
                data = data[key]
            except (KeyError, TypeError, IndexError):
                return default
        return data

    @staticmethod
    def extract_want_count(tags_content: str) -> int:
        """从标签内容中提取"人想要"的数字

        Args:
            tags_content: 标签内容字符串

        Returns:
            int: 想要人数
        """
        try:
            if not tags_content or "人想要" not in tags_content:
                return 0

            pattern = r'(\d+(?:\.\d+)?(?:万)?)\s*人想要'
            match = re.search(pattern, tags_content)

            if match:
                number_str = match.group(1)
                if '万' in number_str:
                    number = float(number_str.replace('万', '')) * 10000
                    return int(number)
                else:
                    return int(float(number_str))

            return 0
        except Exception as e:
            logger.warning(f"提取想要人数失败: {str(e)}")
            return 0

    @staticmethod
    def parse_price(price_parts: Any) -> str:
        """解析价格数据

        Args:
            price_parts: 价格数据

        Returns:
            str: 格式化后的价格字符串
        """
        price = "价格异常"

        if isinstance(price_parts, (int, float)):
            return f"¥{price_parts}"

        if not isinstance(price_parts, list):
            return price

        try:
            price = "".join([str(p.get("text", "")) for p in price_parts if isinstance(p, dict)])
            price = price.replace("当前价", "").strip()

            if price and price != "价格异常":
                clean_price = price.replace('¥', '').strip()

                if "万" in clean_price:
                    try:
                        numeric_price = clean_price.replace('万', '').strip()
                        price_value = float(numeric_price) * 10000
                        price = f"¥{price_value:.0f}"
                    except ValueError:
                        price = f"¥{clean_price}"
                else:
                    if clean_price and (clean_price[0].isdigit() or clean_price.replace('.', '').isdigit()):
                        price = f"¥{clean_price}"
                    else:
                        price = clean_price if clean_price else "价格异常"

        except Exception as e:
            logger.warning(f"解析价格失败: {str(e)}")

        return price

    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """格式化时间戳

        Args:
            timestamp: 时间戳字符串

        Returns:
            str: 格式化后的时间字符串
        """
        if not timestamp or not timestamp.isdigit():
            return "未知时间"

        try:
            return datetime.fromtimestamp(int(timestamp) / 1000).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return "未知时间"

    async def parse_real_item(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析真实的闲鱼商品数据

        Args:
            item_data: 商品原始数据

        Returns:
            Optional[Dict[str, Any]]: 解析后的商品信息，失败返回None
        """
        try:
            main_data = await self.safe_get(item_data, "data", "item", "main", "exContent", default={})
            click_params = await self.safe_get(item_data, "data", "item", "main", "clickParam", "args", default={})

            title = await self.safe_get(main_data, "title", default="未知标题")

            price_parts = await self.safe_get(main_data, "price", default=[])
            price = self.parse_price(price_parts)

            fish_tags_content = ""
            fish_tags = await self.safe_get(main_data, "fishTags", default={})

            for tag_type, tag_data in fish_tags.items():
                if isinstance(tag_data, dict) and "tagList" in tag_data:
                    tag_list = tag_data.get("tagList", [])
                    for tag_item in tag_list:
                        if isinstance(tag_item, dict) and "data" in tag_item:
                            content = tag_item["data"].get("content", "")
                            if content and "人想要" in content:
                                fish_tags_content = content
                                break
                    if fish_tags_content:
                        break

            area = await self.safe_get(main_data, "area", default="地区未知")
            seller = await self.safe_get(main_data, "userNickName", default="匿名卖家")
            raw_link = await self.safe_get(item_data, "data", "item", "main", "targetUrl", default="")
            image_url = await self.safe_get(main_data, "picUrl", default="")

            item_id = await self.safe_get(click_params, "item_id", default="未知ID")

            publish_timestamp = click_params.get("publishTime", "")
            publish_time = self.format_timestamp(publish_timestamp)

            want_count = self.extract_want_count(fish_tags_content)

            return {
                "item_id": item_id,
                "title": title,
                "price": price,
                "seller_name": seller,
                "item_url": raw_link.replace("fleamarket://", "https://www.goofish.com/"),
                "main_image": f"https:{image_url}" if image_url and not image_url.startswith("http") else image_url,
                "publish_time": publish_time,
                "tags": [fish_tags_content] if fish_tags_content else [],
                "area": area,
                "want_count": want_count,
                "raw_data": item_data
            }

        except Exception as e:
            logger.warning(f"解析真实商品数据失败: {str(e)}")
            return None

    async def parse_item_old(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析单个商品数据（旧版兼容）

        Args:
            item_data: 商品原始数据

        Returns:
            Optional[Dict[str, Any]]: 解析后的商品信息
        """
        try:
            item_id = (item_data.get('id') or
                      item_data.get('itemId') or
                      item_data.get('item_id') or
                      item_data.get('spuId') or '')

            title = (item_data.get('title') or
                    item_data.get('name') or
                    item_data.get('itemTitle') or
                    item_data.get('subject') or '')

            price_raw = (item_data.get('price') or
                        item_data.get('priceText') or
                        item_data.get('currentPrice') or
                        item_data.get('realPrice') or '')

            if isinstance(price_raw, (int, float)):
                price = str(price_raw)
            elif isinstance(price_raw, str):
                price = price_raw.replace('¥', '').replace('元', '').strip()
            else:
                price = '价格面议'

            seller_info = (item_data.get('seller') or
                          item_data.get('user') or
                          item_data.get('owner') or {})

            seller_name = ''
            if seller_info:
                seller_name = (seller_info.get('nick') or
                              seller_info.get('nickname') or
                              seller_info.get('name') or
                              seller_info.get('userName') or '匿名用户')

            if item_id:
                item_url = f"https://www.goofish.com/item?id={item_id}"
            else:
                item_url = item_data.get('url', item_data.get('link', ''))

            publish_time = (item_data.get('publishTime') or
                           item_data.get('createTime') or
                           item_data.get('gmtCreate') or
                           item_data.get('time') or '')

            if publish_time and isinstance(publish_time, (int, float)):
                publish_time = datetime.fromtimestamp(publish_time / 1000).strftime('%Y-%m-%d')

            tags = item_data.get('tags', item_data.get('labels', []))
            tag_names = []
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, dict):
                        tag_name = (tag.get('name') or
                                   tag.get('text') or
                                   tag.get('label') or '')
                        if tag_name:
                            tag_names.append(tag_name)
                    elif isinstance(tag, str):
                        tag_names.append(tag)

            images = (item_data.get('images') or
                     item_data.get('pics') or
                     item_data.get('pictures') or
                     item_data.get('imgList') or [])

            main_image = ''
            if images and len(images) > 0:
                if isinstance(images[0], str):
                    main_image = images[0]
                elif isinstance(images[0], dict):
                    main_image = (images[0].get('url') or
                                 images[0].get('src') or
                                 images[0].get('image') or '')

            if not main_image:
                main_image = f'https://via.placeholder.com/200x200?text={title[:10] if title else "商品"}...'

            return {
                'item_id': item_id,
                'title': title,
                'price': price,
                'seller_name': seller_name,
                'item_url': item_url,
                'publish_time': publish_time,
                'tags': tag_names,
                'main_image': main_image,
                'raw_data': item_data
            }

        except Exception as e:
            logger.warning(f"解析商品数据失败: {str(e)}")
            return None

    def generate_mock_items(self, keyword: str, page: int, page_size: int) -> List[Dict[str, Any]]:
        """生成模拟商品数据

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            List[Dict[str, Any]]: 模拟商品列表
        """
        mock_items = []
        start_index = (page - 1) * page_size

        for i in range(page_size):
            item_index = start_index + i + 1
            mock_items.append({
                'item_id': f'mock_{keyword}_{item_index}',
                'title': f'{keyword}相关商品 #{item_index} [模拟数据]',
                'price': f'{100 + item_index * 10}',
                'seller_name': f'卖家{item_index}',
                'item_url': f'https://www.goofish.com/item?id=mock_{keyword}_{item_index}',
                'publish_time': '2025-07-28',
                'tags': [f'标签{i+1}', f'分类{i+1}'],
                'main_image': f'https://via.placeholder.com/200x200?text={keyword}商品{item_index}',
                'raw_data': {
                    'mock': True,
                    'keyword': keyword,
                    'index': item_index
                }
            })

        return mock_items
