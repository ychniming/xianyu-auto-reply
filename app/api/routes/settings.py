"""设置管理路由模块

提供系统设置、用户设置、通知配置等接口
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loguru import logger
import json
import time
from threading import Lock

from app.api.dependencies import get_current_user

router = APIRouter(prefix="", tags=["设置管理"])


class QQOpenIDSessionManager:
    """QQ OpenID 会话管理器（线程安全）"""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def create_session(self, session_id: str, app_id: str, bot_secret: str) -> None:
        """创建新会话"""
        with self._lock:
            self._sessions[session_id] = {
                'status': 'starting',
                'openid': None,
                'error': None,
                'app_id': app_id,
                'bot_secret': bot_secret[:10] + '...' if len(bot_secret) > 10 else bot_secret,
                'created_at': time.time()
            }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        with self._lock:
            return self._sessions.get(session_id)

    def update_session(self, session_id: str, **kwargs) -> None:
        """更新会话"""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].update(kwargs)

    def remove_session(self, session_id: str) -> None:
        """删除会话"""
        with self._lock:
            self._sessions.pop(session_id, None)

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        with self._lock:
            return session_id in self._sessions


_openid_session_manager = QQOpenIDSessionManager()

# -------------------- 请求模型 --------------------
class NotificationChannelIn(BaseModel):
    name: str
    type: str = "qq"
    config: str


class NotificationChannelUpdate(BaseModel):
    name: str
    config: str
    enabled: bool = True


class MessageNotificationIn(BaseModel):
    channel_id: int
    enabled: bool = True


class SystemSettingIn(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


# -------------------- 通知渠道路由 --------------------
@router.get('/notification-channels')
def list_notification_channels(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取所有通知渠道"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        return db_manager.get_notification_channels(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/notification-channels')
def create_notification_channel(channel: NotificationChannelIn, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """创建通知渠道"""
    try:
        from app.repositories import db_manager
        # 必须传递 user_id，不能为 None
        logger.info(f"创建通知渠道：current_user={current_user}, channel={channel.name}")
        if not current_user:
            logger.warning("用户未登录")
            raise HTTPException(status_code=401, detail="请先登录")
        user_id = current_user['user_id']
        logger.info(f"用户 ID: {user_id}")
        channel_id = db_manager.create_notification_channel(
            name=channel.name,
            channel_type=channel.type,
            config=channel.config,
            user_id=user_id
        )
        logger.info(f"创建成功：channel_id={channel_id}")
        return {'msg': 'created', 'id': channel_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建通知渠道失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/notification-channels/{channel_id}')
def get_notification_channel(channel_id: int, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取通知渠道详情"""
    try:
        from app.repositories import db_manager
        channel = db_manager.get_notification_channel(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="通知渠道不存在")
        return channel
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/notification-channels/{channel_id}')
def update_notification_channel(channel_id: int, channel: NotificationChannelUpdate, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新通知渠道"""
    try:
        from app.repositories import db_manager
        db_manager.update_notification_channel(
            channel_id=channel_id,
            name=channel.name,
            config=channel.config,
            enabled=channel.enabled
        )
        return {'msg': 'updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/notification-channels/{channel_id}')
def delete_notification_channel(channel_id: int, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除通知渠道"""
    try:
        from app.repositories import db_manager
        db_manager.delete_notification_channel(channel_id)
        return {'msg': 'deleted'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 消息通知路由 --------------------
@router.get('/message-notifications')
def list_message_notifications(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取所有账号的消息通知配置"""
    try:
        from app.repositories import db_manager
        return db_manager.get_all_message_notifications()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/message-notifications/{cid}')
def get_message_notifications(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取账号的消息通知配置"""
    try:
        from app.repositories import db_manager
        return db_manager.get_account_notifications(cid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/message-notifications/{cid}')
def set_message_notification(cid: str, notification: MessageNotificationIn, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """设置账号的消息通知"""
    try:
        from app.repositories import db_manager
        db_manager.set_message_notification(cid, notification.channel_id, notification.enabled)
        return {'msg': 'updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/message-notifications/account/{cid}')
def delete_account_notifications(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除账号的所有消息通知配置"""
    try:
        from app.repositories import db_manager
        db_manager.delete_account_notifications(cid)
        return {'msg': 'deleted'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/message-notifications/{notification_id}')
def delete_message_notification(notification_id: int, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除消息通知配置"""
    try:
        from app.repositories import db_manager
        db_manager.delete_message_notification(notification_id)
        return {'msg': 'deleted'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 系统设置路由 --------------------
@router.get("/system-settings")
def list_system_settings(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取所有系统设置"""
    try:
        from app.repositories import db_manager
        return db_manager.get_all_system_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/system-settings/{key}")
def update_system_setting(key: str, setting: SystemSettingIn, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新系统设置"""
    try:
        from app.repositories import db_manager
        db_manager.set_system_setting(key, setting.value, setting.description)
        return {'msg': 'updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/system-settings/{key}")
def delete_system_setting(key: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除系统设置"""
    try:
        return {'msg': 'deleted'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 用户设置路由 --------------------
@router.get('/user-settings')
def list_user_settings(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取当前用户设置"""
    try:
        from app.repositories import db_manager
        if not current_user:
            raise HTTPException(status_code=401, detail="未授权")
        user_id = current_user['user_id']
        settings = db_manager.users.get_user_settings(user_id)
        return settings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/user-settings/{key}')
def update_user_setting(key: str, value: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新用户设置"""
    try:
        from app.repositories import db_manager
        if not current_user:
            raise HTTPException(status_code=401, detail="未授权")
        user_id = current_user['user_id']
        db_manager.users.set_user_setting(user_id, key, value)
        return {'msg': 'updated'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/user-settings/{key}')
def get_user_setting(key: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取用户设置"""
    try:
        from app.repositories import db_manager
        if not current_user:
            raise HTTPException(status_code=401, detail="未授权")
        user_id = current_user['user_id']
        value = db_manager.users.get_user_setting(user_id, key)
        return {'key': key, 'value': value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- AI回复设置路由 --------------------
@router.get("/ai-reply-settings/{cookie_id}")
def get_ai_reply_settings(cookie_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取AI回复设置"""
    try:
        from app.repositories import db_manager
        return db_manager.get_ai_reply_settings(cookie_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ai-reply-settings/{cookie_id}")
def update_ai_reply_settings(cookie_id: str, settings: Dict, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新AI回复设置"""
    try:
        from app.repositories import db_manager
        db_manager.save_ai_reply_settings(cookie_id, settings)
        return {'msg': 'updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-reply-settings")
def list_all_ai_reply_settings(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取所有AI回复设置"""
    try:
        from app.repositories import db_manager
        return db_manager.get_all_ai_reply_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-reply-test/{cookie_id}")
async def test_ai_reply(cookie_id: str, message: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """测试AI回复"""
    try:
        from app.core.ai_reply_engine import ai_reply_engine
        result = await ai_reply_engine.generate_reply(cookie_id, message)
        return {'success': True, 'reply': result}
    except Exception as e:
        logger.error(f"AI回复测试失败: {str(e)}")
        return {'success': False, 'error': str(e)}


# -------------------- 缓存管理 --------------------
@router.post("/system/reload-cache")
def reload_cache(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """重新加载缓存"""
    try:
        return {'msg': 'cache reloaded'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- QQ OpenID 获取 --------------------
class QQOpenIDRequest(BaseModel):
    app_id: str
    bot_secret: str


async def _get_access_token(app_id: str, bot_secret: str, session_id: str) -> Optional[str]:
    """获取QQ access token

    Args:
        app_id: QQ应用ID
        bot_secret: QQ应用密钥
        session_id: 会话ID

    Returns:
        Optional[str]: access_token，获取失败返回None
    """
    import aiohttp

    url = "https://bots.qq.com/app/getAppAccessToken"
    data = {
        "appId": app_id,
        "clientSecret": bot_secret
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, timeout=10) as response:
            if response.status != 200:
                error_text = await response.text()
                _openid_session_manager.update_session(
                    session_id,
                    status='error',
                    error=f"获取Token失败: {error_text}"
                )
                return None

            result = await response.json()
            access_token = result.get('access_token')

            if not access_token:
                _openid_session_manager.update_session(
                    session_id,
                    status='error',
                    error="获取Token失败: 无返回token"
                )
                return None

            return access_token


async def _get_gateway_url(access_token: str, session_id: str) -> Optional[str]:
    """获取QQ WebSocket Gateway URL

    Args:
        access_token: QQ access token
        session_id: 会话ID

    Returns:
        Optional[str]: gateway URL，获取失败返回None
    """
    import aiohttp

    gateway_url = "https://sandbox.api.sgroup.qq.com/gateway"
    headers = {"Authorization": f"QQBot {access_token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(gateway_url, headers=headers, timeout=10) as response:
            if response.status != 200:
                error_text = await response.text()
                _openid_session_manager.update_session(
                    session_id,
                    status='error',
                    error=f"获取Gateway失败: {error_text}"
                )
                return None

            result = await response.json()
            return result.get('url')


async def _listen_for_openid_messages(ws, session_id: str, access_token: str) -> Optional[str]:
    """监听OpenID消息

    Args:
        ws: WebSocket连接
        session_id: 会话ID
        access_token: QQ access token

    Returns:
        Optional[str]: 获取的openid，超时返回None
    """
    import asyncio
    import websockets

    auth_data = {
        "op": 2,
        "d": {
            "token": f"QQBot {access_token}",
            "intents": 33554432,
            "shard": [0, 1],
            "properties": {
                "$os": "windows",
                "$browser": "chrome",
                "$device": "pc"
            }
        }
    }
    await ws.send(json.dumps(auth_data))

    start_time = time.time()
    timeout = 120

    while time.time() - start_time < timeout:
        try:
            message = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(message)

            op = data.get('op')
            event_type = data.get('t')

            if event_type in ('C2C_MESSAGE_CREATE', 'C2C_MSG_RECEIVE'):
                openid = data.get('d', {}).get('author', {}).get('user_openid')
                if openid:
                    _openid_session_manager.update_session(
                        session_id,
                        status='success',
                        openid=openid
                    )
                    logger.info(f"捕获到 OpenID: {openid}")
                    return openid

        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"处理消息错误: {e}")
            continue

    _openid_session_manager.update_session(
        session_id,
        status='timeout',
        error="监听超时(120秒)，请给机器人发送消息后重试"
    )
    return None


async def _execute_openid_listener(session_id: str, app_id: str, bot_secret: str) -> None:
    """执行OpenID监听任务

    Args:
        session_id: 会话ID
        app_id: QQ应用ID
        bot_secret: QQ应用密钥
    """
    import websockets

    try:
        _openid_session_manager.update_session(session_id, status='connecting')

        access_token = await _get_access_token(app_id, bot_secret, session_id)
        if not access_token:
            return

        ws_url = await _get_gateway_url(access_token, session_id)
        if not ws_url:
            return

        _openid_session_manager.update_session(session_id, status='listening')

        async with websockets.connect(ws_url) as ws:
            await _listen_for_openid_messages(ws, session_id, access_token)

    except Exception as e:
        logger.error(f"OpenID监听异常: {e}")
        _openid_session_manager.update_session(
            session_id,
            status='error',
            error=str(e)
        )


@router.post('/qq/start-openid-listener')
async def start_qq_openid_listener(request: QQOpenIDRequest, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """启动 QQ OpenID 监听器"""
    import uuid
    import asyncio

    session_id = str(uuid.uuid4())

    _openid_session_manager.create_session(session_id, request.app_id, request.bot_secret)

    asyncio.create_task(_execute_openid_listener(session_id, request.app_id, request.bot_secret))

    return {
        'session_id': session_id,
        'status': 'started',
        'message': '监听器已启动，请给机器人发送消息获取OpenID'
    }


@router.get('/qq/check-openid/{session_id}')
async def check_qq_openid(session_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """检查 OpenID 获取状态"""
    if not _openid_session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = _openid_session_manager.get_session(session_id)

    if session['status'] == 'success':
        openid = session['openid']
        _openid_session_manager.remove_session(session_id)
        return {
            'status': 'success',
            'openid': openid
        }
    elif session['status'] == 'error' or session['status'] == 'timeout':
        error = session.get('error', '未知错误')
        _openid_session_manager.remove_session(session_id)
        return {
            'status': 'error',
            'error': error
        }
    else:
        return {
            'status': session['status'],
            'message': _get_status_message(session['status'])
        }


def _get_status_message(status: str) -> str:
    """获取状态消息"""
    messages = {
        'starting': '正在启动监听器...',
        'connecting': '正在连接 QQ 开放平台...',
        'listening': '正在监听消息，请给机器人发送消息...'
    }
    return messages.get(status, f'状态: {status}')


class QQTestMessageRequest(BaseModel):
    app_id: str
    bot_secret: str
    user_openid: str


@router.post('/qq/send-test-message')
async def send_qq_test_message(request: QQTestMessageRequest, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """发送 QQ 测试消息"""
    import aiohttp
    
    try:
        url = "https://bots.qq.com/app/getAppAccessToken"
        data = {
            "appId": request.app_id,
            "clientSecret": request.bot_secret
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, timeout=10) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {'success': False, 'error': f'获取Token失败: {error_text}'}
                
                result = await response.json()
                access_token = result.get('access_token')
                
                if not access_token:
                    return {'success': False, 'error': '获取Token失败: 无返回token'}
        
        base_url = "https://sandbox.api.sgroup.qq.com"
        send_url = f"{base_url}/v2/users/{request.user_openid}/messages"
        
        headers = {
            "Authorization": f"QQBot {access_token}",
            "Content-Type": "application/json"
        }
        
        message_data = {
            "content": f"🔔 闲鱼自动回复系统测试消息\n\n这是一条测试消息，表示 QQ 机器人配置成功！\n\n发送时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "msg_type": 0
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(send_url, json=message_data, headers=headers, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"QQ测试消息发送成功: {result.get('id')}")
                    return {
                        'success': True,
                        'message': '测试消息发送成功！请检查 QQ 是否收到消息。',
                        'msg_id': result.get('id')
                    }
                else:
                    error_text = await response.text()
                    logger.warning(f"QQ测试消息发送失败: {response.status} - {error_text}")
                    return {'success': False, 'error': f'发送失败({response.status}): {error_text}'}
                    
    except Exception as e:
        logger.error(f"发送QQ测试消息异常: {e}")
        return {'success': False, 'error': str(e)}
