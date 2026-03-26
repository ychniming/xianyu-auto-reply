#!/usr/bin/env python3
"""
闲鱼扫码登录工具
基于API接口实现二维码生成和Cookie获取（参照myfish-main项目）
"""

import asyncio
import time
import uuid
import json
import re
import threading
from random import random
from typing import Optional, Dict, Any
import httpx
import qrcode
import qrcode.constants
from loguru import logger


def generate_headers():
    """生成请求头"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }


class GetLoginParamsError(Exception):
    """获取登录参数错误"""


class GetLoginQRCodeError(Exception):
    """获取登录二维码失败"""


class NotLoginError(Exception):
    """未登录错误"""


class QRLoginSession:
    """二维码登录会话"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.status = 'waiting'  # waiting, scanned, success, expired, cancelled, verification_required
        self.qr_code_url = None
        self.qr_content = None
        self.cookies = {}
        self.unb = None
        self.created_time = time.time()
        self.expire_time = 600  # 10 分钟过期（给用户足够时间完成验证）
        self.params = {}  # 存储登录参数
        self.verification_url = None  # 风控验证 URL
        self.processed = False  # 标记是否已处理，防止重复处理

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_time > self.expire_time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'status': self.status,
            'qr_code_url': self.qr_code_url,
            'created_time': self.created_time,
            'is_expired': self.is_expired()
        }


class QRLoginManager:
    """二维码登录管理器"""

    MAX_SESSIONS = 100
    CLEANUP_THRESHOLD = 50
    LAZY_CLEANUP_CHANCE = 0.1

    def __init__(self):
        self.sessions: Dict[str, QRLoginSession] = {}
        self._lock = threading.Lock()
        self.headers = generate_headers()
        self.host = "https://passport.goofish.com"
        self.api_mini_login = f"{self.host}/mini_login.htm"
        self.api_generate_qr = f"{self.host}/newlogin/qrcode/generate.do"
        self.api_scan_status = f"{self.host}/newlogin/qrcode/query.do"
        self.api_h5_tk = "https://h5api.m.goofish.com/h5/mtop.gaia.nodejs.gaia.idle.data.gw.v2.index.get/1.0/"
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval: int = 300
        self._last_cleanup_count: int = 0

    def _cookie_marshal(self, cookies: dict) -> str:
        """将Cookie字典转换为字符串"""
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])

    async def _get_mh5tk(self, session: QRLoginSession) -> dict:
        """获取m_h5_tk和m_h5_tk_enc"""
        params = {
            "jsv": "2.7.2",
            "appKey": "34839810",
            "t": int(time.time()),
            "sign": "",
            "v": "1.0",
            "type": "originaljson",
            "accountSite": "xianyu",
            "dataType": "json",
            "timeout": 20000,
            "api": "mtop.gaia.nodejs.gaia.idle.data.gw.v2.index.get",
            "sessionOption": "AutoLoginOnly",
            "spm_cnt": "a21ybx.home.0.0",
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.post(
                self.api_h5_tk, params=params, headers=self.headers
            )
            cookies = {}
            for k, v in resp.cookies.items():
                cookies[k] = v
                session.cookies[k] = v
            return cookies

    async def _get_login_params(self, session: QRLoginSession) -> dict:
        """获取二维码登录时需要的表单参数"""
        params = {
            "lang": "zh_cn",
            "appName": "xianyu",
            "appEntrance": "web",
            "styleType": "vertical",
            "bizParams": "",
            "notLoadSsoView": False,
            "notKeepLogin": False,
            "isMobile": False,
            "qrCodeFirst": False,
            "stie": 77,
            "rnd": random(),
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(
                self.api_mini_login,
                params=params,
                cookies=session.cookies,
                headers=self.headers,
            )

            # 正则匹配需要的json数据
            pattern = r"window\.viewData\s*=\s*(\{.*?\});"
            match = re.search(pattern, resp.text)
            if match:
                json_string = match.group(1)
                view_data = json.loads(json_string)
                data = view_data.get("loginFormData")
                if data:
                    data["umidTag"] = "SERVER"
                    session.params.update(data)
                    return data
                else:
                    raise GetLoginParamsError("未找到loginFormData")
            else:
                raise GetLoginParamsError("获取登录参数失败")
    
    async def generate_qr_code(self) -> Dict[str, Any]:
        """生成二维码"""
        try:
            # 创建新的会话
            session_id = str(uuid.uuid4())
            session = QRLoginSession(session_id)

            # 1. 获取m_h5_tk
            await self._get_mh5tk(session)
            logger.info(f"获取m_h5_tk成功: {session_id}")

            # 2. 获取登录参数
            login_params = await self._get_login_params(session)
            logger.info(f"获取登录参数成功: {session_id}")

            # 3. 生成二维码
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(
                    self.api_generate_qr,
                    params=login_params,
                    headers=self.headers
                )
                results = resp.json()

                if results.get("content", {}).get("success") == True:
                    # 更新会话参数
                    session.params.update({
                        "t": results["content"]["data"]["t"],
                        "ck": results["content"]["data"]["ck"],
                    })

                    # 获取二维码内容
                    qr_content = results["content"]["data"]["codeContent"]
                    session.qr_content = qr_content

                    # 生成二维码图片（base64格式）
                    qr = qrcode.QRCode(
                        version=5,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=2,
                    )
                    qr.add_data(qr_content)
                    qr.make()

                    # 将二维码转换为base64
                    from io import BytesIO
                    import base64

                    qr_img = qr.make_image()
                    buffer = BytesIO()
                    qr_img.save(buffer, format='PNG')
                    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
                    qr_data_url = f"data:image/png;base64,{qr_base64}"

                    session.qr_code_url = qr_data_url
                    session.status = 'waiting'

                    # 线程安全地保存会话
                    with self._lock:
                        self.sessions[session_id] = session

                    # 启动状态检查任务
                    asyncio.create_task(self._monitor_qr_status(session_id))

                    # 启动自动清理任务
                    asyncio.create_task(self.start_auto_cleanup())

                    # 检查是否需要清理
                    self._cleanup_if_needed()

                    # 尝试懒清理
                    self._maybe_lazy_cleanup()

                    logger.info(f"二维码生成成功: {session_id}")
                    return {
                        'success': True,
                        'session_id': session_id,
                        'qr_code_url': qr_data_url
                    }
                else:
                    raise GetLoginQRCodeError("获取登录二维码失败")

        except Exception as e:
            logger.error(f"生成二维码失败: {e}")
            return {'success': False, 'message': f'生成二维码失败: {str(e)}'}

    async def start_auto_cleanup(self) -> None:
        """启动自动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
            logger.info("会话自动清理任务已启动")

    async def stop_auto_cleanup(self) -> None:
        """停止自动清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("会话自动清理任务已停止")

    async def _auto_cleanup_loop(self) -> None:
        """自动清理循环"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                cleaned = self.cleanup_expired_sessions()
                session_count = self.get_session_count()
                logger.debug(f"自动清理完成，清理了 {cleaned} 个会话，当前会话数: {session_count}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自动清理异常: {e}")

    async def _poll_qrcode_status(self, session: QRLoginSession) -> httpx.Response:
        """获取二维码扫描状态"""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.post(
                self.api_scan_status,
                data=session.params,
                cookies=session.cookies,
                headers=self.headers,
            )
            return resp

    async def _monitor_qr_status(self, session_id: str):
        """监控二维码状态"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return

            logger.info(f"开始监控二维码状态: {session_id}")

            # 监控登录状态 - 使用会话的过期时间
            max_wait_time = session.expire_time
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                try:
                    # 检查会话是否还存在
                    if session_id not in self.sessions:
                        break

                    # 轮询二维码状态
                    resp = await self._poll_qrcode_status(session)
                    qrcode_status = (
                        resp.json()
                        .get("content", {})
                        .get("data", {})
                        .get("qrCodeStatus")
                    )

                    if qrcode_status == "CONFIRMED":
                        # 登录确认
                        if (
                            resp.json()
                            .get("content", {})
                            .get("data", {})
                            .get("iframeRedirect")
                            is True
                        ):
                            # 账号被风控，需要手机验证
                            session.status = 'verification_required'
                            iframe_url = (
                                resp.json()
                                .get("content", {})
                                .get("data", {})
                                .get("iframeRedirectUrl")
                            )
                            session.verification_url = iframe_url
                            logger.warning(f"账号被风控，需要手机验证: {session_id}, URL: {iframe_url}")
                            # 不退出循环，继续轮询检查验证完成后的状态
                            await asyncio.sleep(2)  # 等待用户完成验证
                            continue
                        else:
                            # 登录成功
                            session.status = 'success'

                            # 保存Cookie
                            for k, v in resp.cookies.items():
                                session.cookies[k] = v
                                if k == 'unb':
                                    session.unb = v

                            logger.info(f"扫码登录成功: {session_id}, UNB: {session.unb}")
                            break

                    elif qrcode_status == "NEW":
                        # 二维码未被扫描，继续轮询
                        # 如果之前是验证状态，检查是否有Cookie返回
                        if session.status == 'verification_required' and resp.cookies:
                            # 验证完成后可能直接返回Cookie
                            session.status = 'success'
                            for k, v in resp.cookies.items():
                                session.cookies[k] = v
                                if k == 'unb':
                                    session.unb = v
                            logger.info(f"验证完成，登录成功: {session_id}, UNB: {session.unb}")
                            break
                        continue

                    elif qrcode_status == "EXPIRED":
                        # 二维码已过期
                        # 如果正在验证中或已登录成功，继续等待验证完成
                        if session.status in ['verification_required', 'verification_complete', 'success']:
                            logger.warning(f"验证期间二维码过期，继续等待验证完成：{session_id}")
                            # 继续轮询，不退出
                            await asyncio.sleep(2)
                            continue
                        else:
                            session.status = 'expired'
                            logger.info(f"二维码已过期：{session_id}")
                            break

                    elif qrcode_status == "SCANED":
                        # 二维码已被扫描，等待确认
                        if session.status == 'waiting':
                            session.status = 'scanned'
                            logger.info(f"二维码已扫描，等待确认: {session_id}")
                        # 如果之前是验证状态，继续等待
                        elif session.status == 'verification_required':
                            logger.info(f"验证中，等待服务器响应: {session_id}")
                            # 检查是否有Cookie返回
                            if resp.cookies:
                                session.status = 'success'
                                for k, v in resp.cookies.items():
                                    session.cookies[k] = v
                                    if k == 'unb':
                                        session.unb = v
                                logger.info(f"验证完成，登录成功: {session_id}, UNB: {session.unb}")
                                break
                    else:
                        # 其他状态，检查是否有Cookie返回
                        if resp.cookies and session.status == 'verification_required':
                            session.status = 'success'
                            for k, v in resp.cookies.items():
                                session.cookies[k] = v
                                if k == 'unb':
                                    session.unb = v
                            logger.info(f"验证完成，登录成功: {session_id}, UNB: {session.unb}")
                            break
                        # 用户取消确认
                        session.status = 'cancelled'
                        logger.info(f"用户取消登录: {session_id}")
                        break

                    await asyncio.sleep(0.8)  # 每0.8秒检查一次

                except Exception as e:
                    logger.error(f"监控二维码状态异常: {e}")
                    await asyncio.sleep(2)

            # 超时处理
            if session.status not in ['success', 'expired', 'cancelled', 'verification_required']:
                session.status = 'expired'
                logger.info(f"二维码监控超时，标记为过期: {session_id}")

        except Exception as e:
            logger.error(f"监控二维码状态失败: {e}")
            if session_id in self.sessions:
                self.sessions[session_id].status = 'expired'
    
    async def check_login(self, session_id: str) -> Dict[str, Any]:
        """检查登录状态（供 API 调用）"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {'status': 'not_found', 'message': '会话不存在，请重新扫码'}
            
            # 检查是否过期
            if session.is_expired() and session.status != 'success':
                logger.warning(f"会话已过期：{session_id}, 状态：{session.status}")
                session.status = 'expired'
                return {'status': 'expired', 'message': '登录会话已过期，请重新扫码'}
            
            # 返回当前状态
            return self.get_session_status(session_id)
            
        except Exception as e:
            logger.error(f"检查登录状态失败：{session_id}, 错误：{e}")
            return {'status': 'error', 'message': str(e)}
    
    async def recheck_login(self, session_id: str) -> Dict[str, Any]:
        """重新检查登录状态（用户点击验证完成按钮后调用）"""
        try:
            return await self.recheck_verification_status(session_id)
        except Exception as e:
            logger.error(f"重新检查登录状态失败：{session_id}, 错误：{e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        session = self.sessions.get(session_id)
        if not session:
            return {'status': 'not_found'}

        # 只有在未成功登录且过期的情况下，才标记为 expired
        # 如果已经登录成功，即使二维码过期也不影响
        if session.is_expired() and session.status not in ['success', 'verification_complete']:
            session.status = 'expired'

        result = {
            'status': session.status,
            'session_id': session_id
        }

        # 如果需要验证，返回验证 URL
        if session.status == 'verification_required' and session.verification_url:
            result['verification_url'] = session.verification_url
            result['message'] = '账号被风控，需要手机验证'

        # 如果登录成功，返回 Cookie 信息
        if session.status == 'success' and session.cookies and session.unb:
            result['cookies'] = self._cookie_marshal(session.cookies)
            result['unb'] = session.unb

        return result

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话（线程安全）

        Returns:
            int: 清理的会话数量
        """
        with self._lock:
            expired_sessions = []
            for session_id, session in self.sessions.items():
                if session.is_expired():
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.sessions[session_id]
                logger.debug(f"清理过期会话: {session_id}")

            self._last_cleanup_count = len(expired_sessions)
            return len(expired_sessions)

    def get_session_cookies(self, session_id: str) -> Optional[Dict[str, str]]:
        """获取会话 Cookie（线程安全）"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and session.status == 'success':
                return {
                    'cookies': self._cookie_marshal(session.cookies),
                    'unb': session.unb
                }
            return None

    def remove_session(self, session_id: str) -> bool:
        """删除会话（线程安全）

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.debug(f"删除会话: {session_id}")
                return True
            return False

    def mark_session_processed(self, session_id: str) -> bool:
        """标记会话已处理，防止重复处理（线程安全）

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功标记
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.processed = True
                logger.debug(f"标记会话已处理: {session_id}")
                return True
            return False

    def is_session_processed(self, session_id: str) -> bool:
        """检查会话是否已处理（线程安全）"""
        with self._lock:
            session = self.sessions.get(session_id)
            return session.processed if session else True

    def _maybe_lazy_cleanup(self) -> None:
        """懒清理 - 按概率触发清理（线程安全）

        当会话数超过清理阈值时，有一定概率触发清理
        """
        with self._lock:
            session_count = len(self.sessions)

        if session_count > self.CLEANUP_THRESHOLD:
            if random() < self.LAZY_CLEANUP_CHANCE:
                cleaned = self.cleanup_expired_sessions()
                if cleaned > 0:
                    logger.debug(f"懒清理触发，清理了 {cleaned} 个过期会话")

    def _cleanup_if_needed(self) -> None:
        """会话数超限时清理（线程安全）"""
        with self._lock:
            session_count = len(self.sessions)

        if session_count >= self.MAX_SESSIONS:
            logger.warning(f"会话数达到上限 ({session_count})，执行紧急清理")
            cleaned = self.cleanup_expired_sessions()
            logger.info(f"紧急清理完成，清理了 {cleaned} 个过期会话")

            with self._lock:
                remaining = len(self.sessions)
            if remaining >= self.MAX_SESSIONS:
                logger.error(f"清理后会话数仍超限，将删除最旧的会话")
                self._force_cleanup_oldest()

    def _force_cleanup_oldest(self) -> int:
        """强制清理最旧的会话（线程安全）

        Returns:
            int: 清理的会话数量
        """
        with self._lock:
            if not self.sessions:
                return 0

            oldest_session_id = None
            oldest_time = float('inf')

            for session_id, session in self.sessions.items():
                if session.created_time < oldest_time:
                    oldest_time = session.created_time
                    oldest_session_id = session_id

            if oldest_session_id:
                del self.sessions[oldest_session_id]
                logger.warning(f"强制清理最旧会话: {oldest_session_id}")
                return 1
            return 0

    def get_session_count(self) -> int:
        """获取当前会话数（线程安全）

        Returns:
            int: 当前会话数
        """
        with self._lock:
            return len(self.sessions)
    
    async def recheck_verification_status(self, session_id: str) -> Dict[str, Any]:
        """重新检查验证状态（用户点击验证完成按钮后调用）"""
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"会话不存在：{session_id}")
            return {'status': 'not_found', 'message': '会话不存在，请重新扫码'}
        
        # 检查是否过期
        if session.is_expired() and session.status != 'success':
            logger.warning(f"会话已过期：{session_id}, 状态：{session.status}")
            session.status = 'expired'
            return {'status': 'expired', 'message': '登录会话已过期，请重新扫码'}
        
        if session.status == 'success':
            # 已经登录成功
            logger.info(f"会话已登录成功：{session_id}")
            return self.get_session_status(session_id)
        
        # 重新检查二维码状态
        try:
            logger.info(f"开始重新检查验证状态：{session_id}, 当前状态：{session.status}")
            resp = await self._poll_qrcode_status(session)
            qrcode_status = (
                resp.json()
                .get("content", {})
                .get("data", {})
                .get("qrCodeStatus")
            )
            
            logger.info(f"重新检查验证状态：{session_id}, QR 状态：{qrcode_status}")
            
            # 检查是否有 Cookie 返回（无论什么状态）
            if resp.cookies:
                session.status = 'success'
                for k, v in resp.cookies.items():
                    session.cookies[k] = v
                    if k == 'unb':
                        session.unb = v
                logger.info(f"验证完成，登录成功（重新检查）: {session_id}, UNB: {session.unb}")
                return self.get_session_status(session_id)
            
            # 如果验证完成，返回 Cookie
            if qrcode_status == "CONFIRMED":
                session.status = 'success'
                for k, v in resp.cookies.items():
                    session.cookies[k] = v
                    if k == 'unb':
                        session.unb = v
                logger.info(f"验证完成，登录成功（重新检查 CONFIRMED）: {session_id}, UNB: {session.unb}")
                return self.get_session_status(session_id)
            
            # 其他状态，返回当前状态
            logger.info(f"验证仍在进行中：{session_id}, 状态：{session.status}")
            return self.get_session_status(session_id)
            
        except Exception as e:
            logger.error(f"重新检查验证状态失败：{session_id}, 错误：{e}")
            return {'status': 'error', 'message': str(e)}


# 全局二维码登录管理器实例
qr_login_manager = QRLoginManager()
