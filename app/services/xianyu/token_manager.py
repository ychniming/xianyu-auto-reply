"""
闲鱼自动回复系统 - Token 管理模块
负责 Token 刷新、Cookie 更新等认证相关功能
"""

import asyncio
import time
import aiohttp
from typing import Optional, Dict, Any
from loguru import logger

from app.utils.xianyu_utils import trans_cookies, generate_sign
from app.services.xianyu.common import safe_str
from configs.config import (
    DEFAULT_HEADERS, API_ENDPOINTS, TOKEN_REFRESH_INTERVAL, TOKEN_RETRY_INTERVAL
)


class TokenManager:
    """Token 管理器 - 负责 Token 刷新和 Cookie 更新"""

    def __init__(self, parent):
        """初始化 Token 管理器

        Args:
            parent: XianyuLive 实例，用于访问共享属性
        """
        self.parent = parent
        self.token_refresh_interval = TOKEN_REFRESH_INTERVAL
        self.token_retry_interval = TOKEN_RETRY_INTERVAL
        self.last_token_refresh_time = 0
        self.current_token = None

    def _safe_str(self, e: Exception) -> str:
        """安全地将异常转换为字符串"""
        try:
            return str(e)
        except Exception:
            try:
                return repr(e)
            except Exception:
                return "未知错误"

    async def refresh_token(self) -> Optional[str]:
        """刷新 token

        Returns:
            Optional[str]: 新的 token，失败返回 None
        """
        try:
            logger.info(f"【{self.parent.cookie_id}】开始刷新 token...")
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
                'api': 'mtop.taobao.idlemessage.pc.login.token',
                'sessionOption': 'AutoLoginOnly',
                'spm_cnt': 'a21ybx.im.0.0',
            }
            data_val = '{"appKey":"444e9908a51d1cb236a27862abc769c9","deviceId":"' + self.parent.device_id + '"}'
            data = {
                'data': data_val,
            }

            token = trans_cookies(self.parent.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.parent.cookies_str).get('_m_h5_tk') else ''

            sign = generate_sign(params['t'], token, data_val)
            params['sign'] = sign

            headers = DEFAULT_HEADERS.copy()
            headers['cookie'] = self.parent.cookies_str

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_ENDPOINTS.get('token'),
                    params=params,
                    data=data,
                    headers=headers
                ) as response:
                    res_json = await response.json()

                    # 先检查是否有新的 Cookie（即使 API 返回错误，Cookie 可能已更新）
                    cookie_updated = False
                    if 'set-cookie' in response.headers:
                        new_cookies = {}
                        for cookie in response.headers.getall('set-cookie', []):
                            if '=' in cookie:
                                name, value = cookie.split(';')[0].split('=', 1)
                                new_cookies[name.strip()] = value.strip()

                        if new_cookies:
                            self.parent.cookies.update(new_cookies)
                            self.parent.cookies_str = '; '.join([f"{k}={v}" for k, v in self.parent.cookies.items()])
                            await self._update_config_cookies()
                            cookie_updated = True
                            logger.info(f"【{self.parent.cookie_id}】Cookie 已更新")

                    if isinstance(res_json, dict):
                        ret_value = res_json.get('ret', [])
                        # 检查是否成功
                        if any('SUCCESS::调用成功' in ret for ret in ret_value):
                            if 'data' in res_json and 'accessToken' in res_json['data']:
                                new_token = res_json['data']['accessToken']
                                self.current_token = new_token
                                self.last_token_refresh_time = time.time()
                                logger.info(f"【{self.parent.cookie_id}】Token 刷新成功")
                                return new_token
                        
                        # 如果 API 返回错误但 Cookie 已更新，尝试从 Cookie 中提取 token
                        if cookie_updated:
                            logger.warning(f"【{self.parent.cookie_id}】API 返回错误但 Cookie 已更新，尝试提取 token...")
                            try:
                                cookies_dict = trans_cookies(self.parent.cookies_str)
                                m_h5_tk = cookies_dict.get('_m_h5_tk', '')
                                if m_h5_tk:
                                    self.current_token = m_h5_tk.split('_')[0]
                                    self.last_token_refresh_time = time.time()
                                    logger.info(f"【{self.parent.cookie_id}】从 Cookie 中提取 token 成功")
                                    return self.current_token
                            except Exception as e:
                                logger.error(f"【{self.parent.cookie_id}】从 Cookie 提取 token 失败：{self._safe_str(e)}")

                    logger.error(f"【{self.parent.cookie_id}】Token 刷新失败：{res_json}")
                    await self.parent.notification_handler.send_token_refresh_notification(
                        f"Token 刷新失败：{res_json}", "token_refresh_failed"
                    )
                    return None

        except Exception as e:
            logger.error(f"Token 刷新异常：{self._safe_str(e)}")
            await self.parent.notification_handler.send_token_refresh_notification(
                f"Token 刷新异常：{str(e)}", "token_refresh_exception"
            )
            return None

    async def _update_config_cookies(self) -> None:
        """更新数据库中的 cookies"""
        try:
            from app.repositories import db_manager

            if hasattr(self.parent, 'cookie_id') and self.parent.cookie_id:
                try:
                    current_user_id = None
                    if hasattr(self.parent, 'user_id') and self.parent.user_id:
                        current_user_id = self.parent.user_id

                    db_manager.save_cookie(self.parent.cookie_id, self.parent.cookies_str, current_user_id)
                    logger.debug(f"已更新 Cookie 到数据库：{self.parent.cookie_id}")
                except Exception as e:
                    logger.error(f"更新数据库 Cookie 失败：{self._safe_str(e)}")
                    await self.parent.notification_handler.send_token_refresh_notification(
                        f"数据库 Cookie 更新失败：{str(e)}", "db_update_failed"
                    )
            else:
                logger.warning("Cookie ID 不存在，无法更新数据库")
                await self.parent.notification_handler.send_token_refresh_notification(
                    "Cookie ID 不存在，无法更新数据库", "cookie_id_missing"
                )
        except Exception as e:
            logger.error(f"更新 Cookie 失败：{self._safe_str(e)}")
            await self.parent.notification_handler.send_token_refresh_notification(
                f"Cookie 更新失败：{str(e)}", "cookie_update_failed"
            )

    async def token_refresh_loop(self) -> None:
        """Token 刷新循环"""
        while True:
            try:
                from app.core import cookie_manager as cm
                if cm.manager and not cm.manager.get_cookie_status(self.parent.cookie_id):
                    logger.info(f"【{self.parent.cookie_id}】账号已禁用，停止 Token 刷新循环")
                    break

                current_time = time.time()
                if current_time - self.last_token_refresh_time >= self.token_refresh_interval:
                    logger.info("Token 即将过期，准备刷新...")
                    new_token = await self.refresh_token()
                    if new_token:
                        logger.info(f"【{self.parent.cookie_id}】Token 刷新成功，准备重新建立连接...")
                        self.parent.connection_restart_flag = True
                        if self.parent.ws:
                            await self.parent.ws.close()
                        break
                    else:
                        logger.error(f"【{self.parent.cookie_id}】Token 刷新失败，将在{self.token_retry_interval // 60}分钟后重试")
                        await self.parent.send_token_refresh_notification(
                            "Token 定时刷新失败，将自动重试", "token_scheduled_refresh_failed"
                        )
                        await asyncio.sleep(self.token_retry_interval)
                        continue
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Token 刷新循环出错：{safe_str(e)}")
                await asyncio.sleep(60)

    def should_refresh_token(self) -> bool:
        """检查是否需要刷新 token

        Returns:
            bool: 是否需要刷新
        """
        if not self.current_token:
            return True
        return (time.time() - self.last_token_refresh_time) >= self.token_refresh_interval
