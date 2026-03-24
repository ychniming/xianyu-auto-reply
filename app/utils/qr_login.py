#!/usr/bin/env python3
"""
闲鱼扫码登录工具
基于API接口实现二维码生成和Cookie获取（参照myfish-main项目）

安全改进：
- 使用secrets模块生成安全的session_id
- 日志脱敏处理
- 配置化参数
- HTTP连接复用
- 异步锁保护
"""

import asyncio
import time
import secrets
import json
import re
from random import random
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import httpx
import qrcode
import qrcode.constants
from loguru import logger

from configs.config import settings


def generate_headers() -> Dict[str, str]:
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


def _mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """脱敏敏感信息
    
    Args:
        value: 需要脱敏的字符串
        visible_chars: 可见字符数
        
    Returns:
        脱敏后的字符串
    """
    if not value:
        return "***"
    if len(value) <= visible_chars:
        return "*" * len(value)
    return f"{value[:visible_chars]}***"


class QRLoginError(Exception):
    """二维码登录基础错误"""
    pass


class GetLoginParamsError(QRLoginError):
    """获取登录参数错误"""
    pass


class GetLoginQRCodeError(QRLoginError):
    """获取登录二维码失败"""
    pass


class QRLoginState(Enum):
    """二维码登录状态枚举"""
    WAITING = auto()
    SCANNED = auto()
    SUCCESS = auto()
    EXPIRED = auto()
    CANCELLED = auto()
    VERIFICATION_REQUIRED = auto()
    ERROR = auto()


@dataclass
class QRLoginSession:
    """二维码登录会话"""
    session_id: str
    user_id: Optional[int] = None
    status: QRLoginState = QRLoginState.WAITING
    qr_code_url: Optional[str] = None
    qr_content: Optional[str] = None
    _cookies: Dict[str, str] = field(default_factory=dict)
    _unb: Optional[str] = None
    created_time: float = field(default_factory=time.time)
    expire_time: int = field(default_factory=lambda: settings.qr_login.expire_time)
    params: Dict[str, Any] = field(default_factory=dict)
    verification_url: Optional[str] = None

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_time > self.expire_time

    @property
    def cookies(self) -> Dict[str, str]:
        """获取Cookie（需要验证状态）"""
        if self.status != QRLoginState.SUCCESS:
            return {}
        return self._cookies.copy()

    @property
    def unb(self) -> Optional[str]:
        """获取UNB"""
        return self._unb

    def set_cookies(self, cookies: Dict[str, str], unb: str) -> None:
        """设置Cookie"""
        self._cookies = cookies.copy()
        self._unb = unb

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于API响应，不包含敏感信息）"""
        return {
            'session_id': self.session_id,
            'status': self.status.name.lower(),
            'created_time': self.created_time,
            'is_expired': self.is_expired()
        }

    def masked_session_id(self) -> str:
        """返回脱敏的session_id"""
        return _mask_sensitive(self.session_id, 8)


class QRLoginManager:
    """二维码登录管理器"""

    def __init__(self):
        self.sessions: Dict[str, QRLoginSession] = {}
        self._lock = asyncio.Lock()
        self.headers = generate_headers()
        self.host = "https://passport.goofish.com"
        self.api_mini_login = f"{self.host}/mini_login.htm"
        self.api_generate_qr = f"{self.host}/newlogin/qrcode/generate.do"
        self.api_scan_status = f"{self.host}/newlogin/qrcode/query.do"
        self.api_h5_tk = "https://h5api.m.goofish.com/h5/mtop.gaia.nodejs.gaia.idle.data.gw.v2.index.get/1.0/"
        self._client: Optional[httpx.AsyncClient] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._last_cleanup_count: int = 0

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端（复用连接）"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self._client

    async def close(self) -> None:
        """清理资源"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.aclose()
            self._client = None

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

        client = await self._get_client()
        resp = await client.post(
            self.api_h5_tk, params=params, headers=self.headers
        )
        cookies = {}
        for k, v in resp.cookies.items():
            cookies[k] = v
            session._cookies[k] = v
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

        client = await self._get_client()
        resp = await client.get(
            self.api_mini_login,
            params=params,
            cookies=session._cookies,
            headers=self.headers,
        )

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

    async def generate_qr_code(self, user_id: int = None) -> Dict[str, Any]:
        """生成二维码
        
        Args:
            user_id: 关联的用户ID，用于权限验证
            
        Returns:
            Dict包含session_id和qr_code_url
        """
        try:
            session_id = secrets.token_urlsafe(32)
            session = QRLoginSession(session_id, user_id=user_id)

            await self._get_mh5tk(session)
            logger.info(f"获取m_h5_tk成功: {session.masked_session_id()}")

            login_params = await self._get_login_params(session)
            logger.info(f"获取登录参数成功: {session.masked_session_id()}")

            client = await self._get_client()
            resp = await client.get(
                self.api_generate_qr,
                params=login_params,
                headers=self.headers
            )
            results = resp.json()

            if results.get("content", {}).get("success") == True:
                session.params.update({
                    "t": results["content"]["data"]["t"],
                    "ck": results["content"]["data"]["ck"],
                })

                qr_content = results["content"]["data"]["codeContent"]
                session.qr_content = qr_content

                qr = qrcode.QRCode(
                    version=5,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=2,
                )
                qr.add_data(qr_content)
                qr.make()

                from io import BytesIO
                import base64

                qr_img = qr.make_image()
                buffer = BytesIO()
                qr_img.save(buffer, format='PNG')
                qr_base64 = base64.b64encode(buffer.getvalue()).decode()
                qr_data_url = f"data:image/png;base64,{qr_base64}"

                session.qr_code_url = qr_data_url
                session.status = QRLoginState.WAITING

                async with self._lock:
                    if len(self.sessions) >= settings.qr_login.max_sessions:
                        await self._cleanup_expired_sessions()
                    self.sessions[session_id] = session

                asyncio.create_task(self._monitor_qr_status(session_id))

                asyncio.create_task(self._start_auto_cleanup())

                logger.info(f"二维码生成成功: {session.masked_session_id()}")
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

    async def _start_auto_cleanup(self) -> None:
        """启动自动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
            logger.debug("会话自动清理任务已启动")

    async def _auto_cleanup_loop(self) -> None:
        """自动清理循环"""
        consecutive_failures = 0
        MAX_FAILURES = 3

        while True:
            try:
                await asyncio.sleep(settings.qr_login.cleanup_interval)
                cleaned = await self._cleanup_expired_sessions()
                consecutive_failures = 0

                async with self._lock:
                    session_count = len(self.sessions)

                if session_count > settings.qr_login.max_sessions * 0.8:
                    logger.warning(f"会话数接近上限: {session_count}/{settings.qr_login.max_sessions}")

                logger.debug(f"自动清理完成，清理了 {cleaned} 个会话，当前会话数: {session_count}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"自动清理异常 ({consecutive_failures}/{MAX_FAILURES}): {e}")

                if consecutive_failures >= MAX_FAILURES:
                    logger.critical("自动清理连续失败")
                    break

    async def _poll_qrcode_status(self, session: QRLoginSession) -> httpx.Response:
        """获取二维码扫描状态"""
        client = await self._get_client()
        resp = await client.post(
            self.api_scan_status,
            data=session.params,
            cookies=session._cookies,
            headers=self.headers,
        )
        return resp

    async def _monitor_qr_status(self, session_id: str) -> None:
        """监控二维码状态"""
        try:
            async with self._lock:
                session = self.sessions.get(session_id)
            if not session:
                return

            logger.info(f"开始监控二维码状态: {session.masked_session_id()}")

            max_wait_time = session.expire_time
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                try:
                    async with self._lock:
                        if session_id not in self.sessions:
                            break

                    resp = await self._poll_qrcode_status(session)
                    qrcode_status = (
                        resp.json()
                        .get("content", {})
                        .get("data", {})
                        .get("qrCodeStatus")
                    )

                    if qrcode_status == "CONFIRMED":
                        if (
                            resp.json()
                            .get("content", {})
                            .get("data", {})
                            .get("iframeRedirect")
                            is True
                        ):
                            session.status = QRLoginState.VERIFICATION_REQUIRED
                            iframe_url = (
                                resp.json()
                                .get("content", {})
                                .get("data", {})
                                .get("iframeRedirectUrl")
                            )
                            session.verification_url = iframe_url
                            logger.warning(f"账号被风控，需要手机验证: {session.masked_session_id()}")
                            await asyncio.sleep(2)
                            continue
                        else:
                            session.status = QRLoginState.SUCCESS
                            for k, v in resp.cookies.items():
                                session._cookies[k] = v
                                if k == 'unb':
                                    session._unb = v
                            logger.info(f"扫码登录成功: {session.masked_session_id()}, UNB: {_mask_sensitive(session._unb)}")
                            break

                    elif qrcode_status == "NEW":
                        if session.status == QRLoginState.VERIFICATION_REQUIRED and resp.cookies:
                            session.status = QRLoginState.SUCCESS
                            for k, v in resp.cookies.items():
                                session._cookies[k] = v
                                if k == 'unb':
                                    session._unb = v
                            logger.info(f"验证完成，登录成功: {session.masked_session_id()}")
                            break
                        continue

                    elif qrcode_status == "EXPIRED":
                        if session.status in [QRLoginState.VERIFICATION_REQUIRED, QRLoginState.SUCCESS]:
                            logger.warning(f"验证期间二维码过期，继续等待: {session.masked_session_id()}")
                            await asyncio.sleep(2)
                            continue
                        else:
                            session.status = QRLoginState.EXPIRED
                            logger.info(f"二维码已过期: {session.masked_session_id()}")
                            break

                    elif qrcode_status == "SCANED":
                        if session.status == QRLoginState.WAITING:
                            session.status = QRLoginState.SCANNED
                            logger.info(f"二维码已扫描，等待确认: {session.masked_session_id()}")
                        elif session.status == QRLoginState.VERIFICATION_REQUIRED:
                            if resp.cookies:
                                session.status = QRLoginState.SUCCESS
                                for k, v in resp.cookies.items():
                                    session._cookies[k] = v
                                    if k == 'unb':
                                        session._unb = v
                                logger.info(f"验证完成，登录成功: {session.masked_session_id()}")
                                break
                    else:
                        if resp.cookies and session.status == QRLoginState.VERIFICATION_REQUIRED:
                            session.status = QRLoginState.SUCCESS
                            for k, v in resp.cookies.items():
                                session._cookies[k] = v
                                if k == 'unb':
                                    session._unb = v
                            logger.info(f"验证完成，登录成功: {session.masked_session_id()}")
                            break
                        session.status = QRLoginState.CANCELLED
                        logger.info(f"用户取消登录: {session.masked_session_id()}")
                        break

                    await asyncio.sleep(settings.qr_login.poll_interval)

                except httpx.TimeoutError:
                    logger.warning(f"请求超时，重试中: {session.masked_session_id()}")
                    await asyncio.sleep(1)
                except httpx.NetworkError as e:
                    logger.error(f"网络错误: {e}")
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"监控二维码状态异常: {e}")
                    await asyncio.sleep(2)

            if session.status not in [QRLoginState.SUCCESS, QRLoginState.EXPIRED, QRLoginState.CANCELLED, QRLoginState.VERIFICATION_REQUIRED]:
                session.status = QRLoginState.EXPIRED
                logger.info(f"二维码监控超时，标记为过期: {session.masked_session_id()}")

        except Exception as e:
            logger.error(f"监控二维码状态失败: {e}")
            async with self._lock:
                if session_id in self.sessions:
                    self.sessions[session_id].status = QRLoginState.EXPIRED

    async def check_login(self, session_id: str, user_id: int = None) -> Dict[str, Any]:
        """检查登录状态（供 API 调用）
        
        Args:
            session_id: 会话ID
            user_id: 当前用户ID，用于权限验证
            
        Returns:
            Dict包含状态信息
        """
        try:
            async with self._lock:
                session = self.sessions.get(session_id)

            if not session:
                return {'status': 'not_found', 'message': '会话不存在，请重新扫码'}

            if user_id is not None and session.user_id is not None and session.user_id != user_id:
                logger.warning(f"用户{user_id}尝试访问他人会话{_mask_sensitive(session_id, 8)}")
                return {'status': 'forbidden', 'message': '无权访问此会话'}

            if session.is_expired() and session.status != QRLoginState.SUCCESS:
                logger.warning(f"会话已过期: {session.masked_session_id()}")
                session.status = QRLoginState.EXPIRED
                return {'status': 'expired', 'message': '登录会话已过期，请重新扫码'}

            return self.get_session_status(session_id)

        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return {'status': 'error', 'message': str(e)}

    async def recheck_login(self, session_id: str, user_id: int = None) -> Dict[str, Any]:
        """重新检查登录状态（用户点击验证完成按钮后调用）"""
        try:
            return await self._recheck_verification_status(session_id, user_id)
        except Exception as e:
            logger.error(f"重新检查登录状态失败: {e}")
            return {'status': 'error', 'message': str(e)}

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        session = self.sessions.get(session_id)
        if not session:
            return {'status': 'not_found'}

        if session.is_expired() and session.status not in [QRLoginState.SUCCESS]:
            session.status = QRLoginState.EXPIRED

        result = {
            'status': session.status.name.lower(),
            'session_id': session_id
        }

        if session.status == QRLoginState.VERIFICATION_REQUIRED and session.verification_url:
            result['verification_url'] = session.verification_url
            result['message'] = '账号被风控，需要手机验证'

        if session.status == QRLoginState.SUCCESS and session._cookies and session._unb:
            result['cookies'] = self._cookie_marshal(session._cookies)
            result['unb'] = session._unb

        return result

    async def _cleanup_expired_sessions(self) -> int:
        """清理过期会话

        Returns:
            int: 清理的会话数量
        """
        async with self._lock:
            expired_sessions = []
            for session_id, session in self.sessions.items():
                if session.is_expired():
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.sessions[session_id]
                logger.debug(f"清理过期会话: {_mask_sensitive(session_id, 8)}")

            self._last_cleanup_count = len(expired_sessions)
            return len(expired_sessions)

    def get_session_count(self) -> int:
        """获取当前会话数"""
        return len(self.sessions)

    async def _recheck_verification_status(self, session_id: str, user_id: int = None) -> Dict[str, Any]:
        """重新检查验证状态"""
        async with self._lock:
            session = self.sessions.get(session_id)

        if not session:
            logger.warning(f"会话不存在: {_mask_sensitive(session_id, 8)}")
            return {'status': 'not_found', 'message': '会话不存在，请重新扫码'}

        if user_id is not None and session.user_id is not None and session.user_id != user_id:
            logger.warning(f"用户{user_id}尝试访问他人会话")
            return {'status': 'forbidden', 'message': '无权访问此会话'}

        if session.is_expired() and session.status != QRLoginState.SUCCESS:
            logger.warning(f"会话已过期: {session.masked_session_id()}")
            session.status = QRLoginState.EXPIRED
            return {'status': 'expired', 'message': '登录会话已过期，请重新扫码'}

        if session.status == QRLoginState.SUCCESS:
            logger.info(f"会话已登录成功: {session.masked_session_id()}")
            return self.get_session_status(session_id)

        try:
            logger.info(f"开始重新检查验证状态: {session.masked_session_id()}")
            resp = await self._poll_qrcode_status(session)
            qrcode_status = (
                resp.json()
                .get("content", {})
                .get("data", {})
                .get("qrCodeStatus")
            )

            logger.info(f"重新检查验证状态: {session.masked_session_id()}, QR状态: {qrcode_status}")

            if resp.cookies:
                session.status = QRLoginState.SUCCESS
                for k, v in resp.cookies.items():
                    session._cookies[k] = v
                    if k == 'unb':
                        session._unb = v
                logger.info(f"验证完成，登录成功: {session.masked_session_id()}")
                return self.get_session_status(session_id)

            if qrcode_status == "CONFIRMED":
                session.status = QRLoginState.SUCCESS
                for k, v in resp.cookies.items():
                    session._cookies[k] = v
                    if k == 'unb':
                        session._unb = v
                logger.info(f"验证完成，登录成功: {session.masked_session_id()}")
                return self.get_session_status(session_id)

            logger.info(f"验证仍在进行中: {session.masked_session_id()}")
            return self.get_session_status(session_id)

        except Exception as e:
            logger.error(f"重新检查验证状态失败: {e}")
            return {'status': 'error', 'message': str(e)}


qr_login_manager = QRLoginManager()
