"""
闲鱼自动回复系统 - 商品API模块
负责商品信息的API调用
"""

import json
import time
import asyncio
from typing import Dict, Any
from loguru import logger

from app.utils.xianyu_utils import trans_cookies, generate_sign
from app.services.xianyu.common import safe_str


class ItemAPI:
    """商品API调用器"""

    def __init__(self, parent):
        self.parent = parent

    def _safe_str(self, obj) -> str:
        """安全转换为字符串"""
        return safe_str(obj)

    async def get_item_info(self, item_id: str, retry_count: int = 0) -> Dict[str, Any]:
        """获取商品信息，自动处理token失效的情况

        Args:
            item_id: 商品ID
            retry_count: 重试次数

        Returns:
            Dict[str, Any]: 商品信息
        """
        if retry_count >= 4:
            logger.error("获取商品信息失败，重试次数过多")
            return {"error": "获取商品信息失败，重试次数过多"}

        if retry_count > 0:
            old_token = self.parent.cookies.get('_m_h5_tk', '').split('_')[0] if self.parent.cookies.get('_m_h5_tk') else ''
            logger.info(f"重试第{retry_count}次，强制刷新token... 当前_m_h5_tk: {old_token}")
            await self.parent.refresh_token()
            new_token = self.parent.cookies.get('_m_h5_tk', '').split('_')[0] if self.parent.cookies.get('_m_h5_tk') else ''
            logger.info(f"重试刷新token完成，新的_m_h5_tk: {new_token}")
        else:
            if not self.parent.current_token or (time.time() - self.parent.last_token_refresh_time) >= self.parent.token_refresh_interval:
                old_token = self.parent.cookies.get('_m_h5_tk', '').split('_')[0] if self.parent.cookies.get('_m_h5_tk') else ''
                logger.info(f"Token过期或不存在，刷新token... 当前_m_h5_tk: {old_token}")
                await self.parent.refresh_token()
                new_token = self.parent.cookies.get('_m_h5_tk', '').split('_')[0] if self.parent.cookies.get('_m_h5_tk') else ''
                logger.info(f"Token刷新完成，新的_m_h5_tk: {new_token}")

        if not self.parent.session:
            await self.parent.create_session()

        params = {
            'jsv': '2.7.2',
            'appKey': '34839810',
            't': str(int(time.time()) * 1000),
            'sign': '',
            'v': '1.0',
            'type': 'originaljson',
            'accountSite': 'xianyu',
            'dataType': 'json',
            'timeout': '20000',
            'api': 'mtop.taobao.idle.pc.detail',
            'sessionOption': 'AutoLoginOnly',
            'spm_cnt': 'a21ybx.im.0.0',
        }

        data_val = json.dumps({"itemId": item_id}, separators=(',', ':'))
        data = {'data': data_val}

        token = trans_cookies(self.parent.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.parent.cookies_str).get('_m_h5_tk') else ''

        sign = generate_sign(params['t'], token, data_val)
        params['sign'] = sign

        try:
            async with self.parent.session.post(
                'https://h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail/1.0/',
                params=params,
                data=data
            ) as response:
                res_json = await response.json()

                if 'set-cookie' in response.headers:
                    new_cookies = {}
                    for cookie in response.headers.getall('set-cookie', []):
                        if '=' in cookie:
                            name, value = cookie.split(';')[0].split('=', 1)
                            new_cookies[name.strip()] = value.strip()

                    if new_cookies:
                        self.parent.cookies.update(new_cookies)
                        self.parent.cookies_str = '; '.join([f"{k}={v}" for k, v in self.parent.cookies.items()])
                        await self.parent.update_config_cookies()
                        logger.debug("已更新Cookie到数据库")

                logger.debug(f"商品信息获取成功: {res_json}")
                if isinstance(res_json, dict):
                    ret_value = res_json.get('ret', [])
                    if not any('SUCCESS::调用成功' in ret for ret in ret_value):
                        logger.warning(f"商品信息API调用失败，错误信息: {ret_value}")
                        await asyncio.sleep(0.5)
                        return await self.get_item_info(item_id, retry_count + 1)
                    else:
                        logger.debug(f"商品信息获取成功: {item_id}")
                        return res_json
                else:
                    logger.error(f"商品信息API返回格式异常: {res_json}")
                    return await self.get_item_info(item_id, retry_count + 1)

        except Exception as e:
            logger.error(f"商品信息API请求异常: {self._safe_str(e)}")
            await asyncio.sleep(0.5)
            return await self.get_item_info(item_id, retry_count + 1)

    async def get_item_list_info(self, page_number: int = 1, page_size: int = 20, retry_count: int = 0) -> Dict[str, Any]:
        """获取商品列表信息，自动处理token失效的情况

        Args:
            page_number: 页码
            page_size: 每页数量
            retry_count: 重试次数

        Returns:
            Dict[str, Any]: 商品列表信息
        """
        if retry_count >= 4:
            logger.error("获取商品信息失败，重试次数过多")
            return {"error": "获取商品信息失败，重试次数过多"}

        if retry_count > 0:
            old_token = trans_cookies(self.parent.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.parent.cookies_str).get('_m_h5_tk') else ''
            logger.info(f"重试第{retry_count}次，强制刷新token... 当前_m_h5_tk: {old_token}")
            await self.parent.refresh_token()
        else:
            if not self.parent.current_token or (time.time() - self.parent.last_token_refresh_time) >= self.parent.token_refresh_interval:
                old_token = trans_cookies(self.parent.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.parent.cookies_str).get('_m_h5_tk') else ''
                logger.info(f"Token过期或不存在，刷新token... 当前_m_h5_tk: {old_token}")
                await self.parent.refresh_token()

        if not self.parent.session:
            await self.parent.create_session()

        params = {
            'jsv': '2.7.2',
            'appKey': '34839810',
            't': str(int(time.time()) * 1000),
            'sign': '',
            'v': '1.0',
            'type': 'originaljson',
            'accountSite': 'xianyu',
            'dataType': 'json',
            'timeout': '20000',
            'api': 'mtop.idle.web.xyh.item.list',
            'sessionOption': 'AutoLoginOnly',
            'spm_cnt': 'a21ybx.im.0.0',
            'spm_pre': 'a21ybx.collection.menu.1.272b5141NafCNK'
        }

        data = {
            'needGroupInfo': False,
            'pageNumber': page_number,
            'pageSize': page_size,
            'groupName': '在售',
            'groupId': '58877261',
            'defaultGroup': True,
            "userId": self.parent.myid
        }

        token = trans_cookies(self.parent.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.parent.cookies_str).get('_m_h5_tk') else ''

        data_val = json.dumps(data, separators=(',', ':'))
        sign = generate_sign(params['t'], token, data_val)
        params['sign'] = sign

        try:
            async with self.parent.session.post(
                'https://h5api.m.goofish.com/h5/mtop.idle.web.xyh.item.list/1.0/',
                params=params,
                data={'data': data_val}
            ) as response:
                res_json = await response.json()

                if 'set-cookie' in response.headers:
                    new_cookies = {}
                    for cookie in response.headers.getall('set-cookie', []):
                        if '=' in cookie:
                            name, value = cookie.split(';')[0].split('=', 1)
                            new_cookies[name.strip()] = value.strip()

                    if new_cookies:
                        self.parent.cookies.update(new_cookies)
                        self.parent.cookies_str = '; '.join([f"{k}={v}" for k, v in self.parent.cookies.items()])
                        await self.parent.update_config_cookies()
                        logger.debug("已更新Cookie到数据库")

                logger.info(f"商品信息获取响应: {res_json}")

                if res_json.get('ret') and res_json['ret'][0] == 'SUCCESS::调用成功':
                    items_data = res_json.get('data', {})
                    card_list = items_data.get('cardList', [])

                    items_list = []
                    for card in card_list:
                        card_data = card.get('cardData', {})
                        if card_data:
                            item_info = {
                                'id': card_data.get('id', ''),
                                'title': card_data.get('title', ''),
                                'price': card_data.get('priceInfo', {}).get('price', ''),
                                'price_text': card_data.get('priceInfo', {}).get('preText', '') + card_data.get('priceInfo', {}).get('price', ''),
                                'category_id': card_data.get('categoryId', ''),
                                'auction_type': card_data.get('auctionType', ''),
                                'item_status': card_data.get('itemStatus', 0),
                                'detail_url': card_data.get('detailUrl', ''),
                                'pic_info': card_data.get('picInfo', {}),
                                'detail_params': card_data.get('detailParams', {}),
                                'track_params': card_data.get('trackParams', {}),
                                'item_label_data': card_data.get('itemLabelDataVO', {}),
                                'card_type': card.get('cardType', 0)
                            }
                            items_list.append(item_info)

                    logger.info(f"成功获取到 {len(items_list)} 个商品")

                    logger.info("=" * 80)
                    logger.info(f"账号 {self.parent.myid} 的商品列表 (第{page_number}页，{len(items_list)} 个商品)")
                    logger.info("=" * 80)

                    for i, item in enumerate(items_list, 1):
                        logger.info(f"商品 {i}: ID={item.get('id', 'N/A')}, 标题={item.get('title', 'N/A')}, 价格={item.get('price_text', 'N/A')}")
                        logger.debug(f"商品 {i} 完整信息: {json.dumps(item, ensure_ascii=False)}")

                    logger.info("=" * 80)
                    logger.info("商品列表获取完成")

                    if items_list:
                        saved_count = await self.parent.item_db.save_items_list_to_db(items_list)
                        logger.info(f"已将 {saved_count} 个商品信息保存到数据库")

                    return {
                        "success": True,
                        "page_number": page_number,
                        "page_size": page_size,
                        "current_count": len(items_list),
                        "items": items_list,
                        "saved_count": saved_count if items_list else 0,
                        "raw_data": items_data
                    }
                else:
                    error_msg = res_json.get('ret', [''])[0] if res_json.get('ret') else ''
                    if 'FAIL_SYS_TOKEN_EXOIRED' in error_msg or 'token' in error_msg.lower():
                        logger.warning(f"Token失效，准备重试: {error_msg}")
                        await asyncio.sleep(0.5)
                        return await self.get_item_list_info(page_number, page_size, retry_count + 1)
                    else:
                        logger.error(f"获取商品信息失败: {res_json}")
                        return {"error": f"获取商品信息失败: {error_msg}"}

        except Exception as e:
            logger.error(f"商品信息API请求异常: {self._safe_str(e)}")
            await asyncio.sleep(0.5)
            return await self.get_item_list_info(page_number, page_size, retry_count + 1)

    async def get_all_items(self, page_size: int = 20, max_pages: int = None) -> Dict[str, Any]:
        """获取所有商品信息（自动分页）

        Args:
            page_size: 每页数量
            max_pages: 最大页数

        Returns:
            Dict[str, Any]: 所有商品信息
        """
        all_items = []
        page_number = 1
        total_saved = 0

        logger.info(f"开始获取所有商品信息，每页{page_size}条")

        while True:
            if max_pages and page_number > max_pages:
                logger.info(f"达到最大页数限制 {max_pages}，停止获取")
                break

            logger.info(f"正在获取第 {page_number} 页...")
            result = await self.get_item_list_info(page_number, page_size)

            if not result.get("success"):
                logger.error(f"获取第 {page_number} 页失败: {result}")
                break

            current_items = result.get("items", [])
            if not current_items:
                logger.info(f"第 {page_number} 页没有数据，获取完成")
                break

            all_items.extend(current_items)
            total_saved += result.get("saved_count", 0)

            logger.info(f"第 {page_number} 页获取到 {len(current_items)} 个商品")

            if len(current_items) < page_size:
                logger.info(f"第 {page_number} 页商品数量({len(current_items)})少于页面大小({page_size})，获取完成")
                break

            page_number += 1
            await asyncio.sleep(1)

        logger.info(f"所有商品获取完成，共 {len(all_items)} 个商品，保存了 {total_saved} 个")

        return {
            "success": True,
            "total_pages": page_number,
            "total_count": len(all_items),
            "total_saved": total_saved,
            "items": all_items
        }
