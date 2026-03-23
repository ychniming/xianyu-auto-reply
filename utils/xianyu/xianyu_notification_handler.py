"""
闲鱼自动回复系统 - 通知处理模块
处理消息通知、Token刷新通知、发货失败通知等
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any

from loguru import logger
from utils.xianyu.common import safe_str


class QQBotClient:
    """QQ开放平台机器人客户端"""
    
    _access_token_cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    async def get_access_token(cls, app_id: str, bot_secret: str) -> Optional[str]:
        """获取QQ机器人Access Token"""
        cache_key = f"{app_id}"
        
        if cache_key in cls._access_token_cache:
            cache_data = cls._access_token_cache[cache_key]
            if time.time() < cache_data['expires_at']:
                return cache_data['token']
        
        try:
            import aiohttp
            
            url = "https://bots.qq.com/app/getAppAccessToken"
            data = {
                "appId": app_id,
                "clientSecret": bot_secret
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        token = result.get('access_token')
                        expires_in_str = result.get('expires_in', '7200')
                        
                        # 确保 expires_in 是整数
                        try:
                            expires_in = int(expires_in_str)
                        except (ValueError, TypeError):
                            expires_in = 7200
                        
                        if token:
                            cls._access_token_cache[cache_key] = {
                                'token': token,
                                'expires_at': time.time() + expires_in - 300
                            }
                            return token
                    
                    logger.warning(f"获取QQ机器人Token失败: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取QQ机器人Token异常: {e}")
            return None
    
    @classmethod
    async def send_private_message(cls, access_token: str, user_openid: str, message: str, sandbox: bool = False) -> bool:
        """发送QQ私聊消息"""
        try:
            import aiohttp
            
            base_url = "https://api.sgroup.qq.com"
            if sandbox:
                base_url = "https://sandbox.api.sgroup.qq.com"
            
            url = f"{base_url}/v2/users/{user_openid}/messages"
            
            headers = {
                "Authorization": f"QQBot {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "content": message,
                "msg_type": 0
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"QQ机器人消息发送成功: {result.get('id')}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.warning(f"QQ机器人消息发送失败: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"QQ机器人消息发送异常: {e}")
            return False


class NotificationHandler:
    """通知处理器"""

    def __init__(self, parent):
        """初始化通知处理器

        Args:
            parent: 父类 XianyuLive 实例
        """
        self.parent = parent

    def _parse_notification_config(self, config: str) -> Dict[str, Any]:
        """解析通知配置数据"""
        try:
            # 尝试解析JSON格式的配置
            return json.loads(config)
        except (json.JSONDecodeError, TypeError):
            # 兼容旧格式（直接字符串）
            return {"config": config}

    async def _send_qq_notification(self, config_data: Dict[str, Any], message: str) -> None:
        """发送QQ通知（支持QQ开放平台机器人，强制使用沙箱环境）"""
        try:
            app_id = config_data.get('app_id', '')
            bot_secret = config_data.get('bot_secret', '')
            user_openid = config_data.get('user_openid', '')
            sandbox = True  # 强制使用沙箱环境，无发送限制
            
            if app_id and bot_secret and user_openid:
                access_token = await QQBotClient.get_access_token(app_id, bot_secret)
                if access_token:
                    success = await QQBotClient.send_private_message(
                        access_token, user_openid, message, sandbox
                    )
                    if success:
                        logger.info(f"QQ机器人通知发送成功: {user_openid}")
                    else:
                        logger.warning(f"QQ机器人通知发送失败")
                else:
                    logger.warning("获取QQ机器人Access Token失败")
            else:
                logger.warning("QQ机器人配置不完整，需要 app_id, bot_secret, user_openid")

        except Exception as e:
            logger.error(f"发送QQ通知异常: {safe_str(e)}")

    async def _send_dingtalk_notification(self, config_data: Dict[str, Any], message: str) -> None:
        """发送钉钉通知"""
        try:
            import aiohttp
            import hmac
            import hashlib
            import base64

            # 解析配置
            webhook_url = config_data.get('webhook_url') or config_data.get('config', '')
            secret = config_data.get('secret', '')

            webhook_url = webhook_url.strip() if webhook_url else ''
            if not webhook_url:
                logger.warning("钉钉通知配置为空")
                return

            # 如果有加签密钥，生成签名
            if secret:
                timestamp = str(round(time.time() * 1000))
                secret_enc = secret.encode('utf-8')
                string_to_sign = f'{timestamp}\n{secret}'
                string_to_sign_enc = string_to_sign.encode('utf-8')
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = base64.b64encode(hmac_code).decode('utf-8')
                webhook_url += f'&timestamp={timestamp}&sign={sign}'

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "闲鱼自动回复通知",
                    "text": message
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=data, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"钉钉通知发送成功")
                    else:
                        logger.warning(f"钉钉通知发送失败: {response.status}")

        except Exception as e:
            logger.error(f"发送钉钉通知异常: {safe_str(e)}")

    async def _send_email_notification(self, config_data: Dict[str, Any], message: str) -> None:
        """发送邮件通知"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # 解析配置
            smtp_server = config_data.get('smtp_server', '')
            smtp_port = int(config_data.get('smtp_port', 587))
            email_user = config_data.get('email_user', '')
            email_password = config_data.get('email_password', '')
            recipient_email = config_data.get('recipient_email', '')

            if not all([smtp_server, email_user, email_password, recipient_email]):
                logger.warning("邮件通知配置不完整")
                return

            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = recipient_email
            msg['Subject'] = "闲鱼自动回复通知"

            # 添加邮件正文
            msg.attach(MIMEText(message, 'plain', 'utf-8'))

            # 发送邮件
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"邮件通知发送成功: {recipient_email}")

        except Exception as e:
            logger.error(f"发送邮件通知异常: {safe_str(e)}")

    async def _send_webhook_notification(self, config_data: Dict[str, Any], message: str) -> None:
        """发送Webhook通知"""
        try:
            import aiohttp

            # 解析配置
            webhook_url = config_data.get('webhook_url', '')
            http_method = config_data.get('http_method', 'POST').upper()
            headers_str = config_data.get('headers', '{}')

            if not webhook_url:
                logger.warning("Webhook通知配置为空")
                return

            # 解析自定义请求头
            try:
                custom_headers = json.loads(headers_str) if headers_str else {}
            except json.JSONDecodeError:
                custom_headers = {}

            # 设置默认请求头
            headers = {'Content-Type': 'application/json'}
            headers.update(custom_headers)

            # 构建请求数据
            data = {
                'message': message,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'xianyu-auto-reply'
            }

            async with aiohttp.ClientSession() as session:
                if http_method == 'POST':
                    async with session.post(webhook_url, json=data, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            logger.info(f"Webhook通知发送成功")
                        else:
                            logger.warning(f"Webhook通知发送失败: {response.status}")
                elif http_method == 'PUT':
                    async with session.put(webhook_url, json=data, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            logger.info(f"Webhook通知发送成功")
                        else:
                            logger.warning(f"Webhook通知发送失败: {response.status}")
                else:
                    logger.warning(f"不支持的HTTP方法: {http_method}")

        except Exception as e:
            logger.error(f"发送Webhook通知异常: {safe_str(e)}")

    async def _send_wechat_notification(self, config_data: Dict[str, Any], message: str) -> None:
        """发送微信通知"""
        try:
            import aiohttp

            # 解析配置
            webhook_url = config_data.get('webhook_url', '')

            if not webhook_url:
                logger.warning("微信通知配置为空")
                return

            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=data, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"微信通知发送成功")
                    else:
                        logger.warning(f"微信通知发送失败: {response.status}")

        except Exception as e:
            logger.error(f"发送微信通知异常: {safe_str(e)}")

    async def _send_telegram_notification(self, config_data: Dict[str, Any], message: str) -> None:
        """发送Telegram通知"""
        try:
            import aiohttp

            # 解析配置
            bot_token = config_data.get('bot_token', '')
            chat_id = config_data.get('chat_id', '')

            if not all([bot_token, chat_id]):
                logger.warning("Telegram通知配置不完整")
                return

            # 构建API URL
            api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=data, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"Telegram通知发送成功")
                    else:
                        logger.warning(f"Telegram通知发送失败: {response.status}")

        except Exception as e:
            logger.error(f"发送Telegram通知异常: {safe_str(e)}")

    async def send_notification(self, send_user_name: str, send_user_id: str, send_message: str, item_id: str = None) -> None:
        """发送消息通知"""
        try:
            from db_manager import db_manager

            # 获取当前账号的通知配置
            notifications = db_manager.get_account_notifications(self.parent.cookie_id)

            if not notifications:
                logger.debug(f"账号 {self.parent.cookie_id} 未配置消息通知")
                return

            # 构建通知消息
            notification_msg = f"🚨 接收消息通知\n\n" \
                             f"账号: {self.parent.cookie_id}\n" \
                             f"买家: {send_user_name} (ID: {send_user_id})\n" \
                             f"商品ID: {item_id or '未知'}\n" \
                             f"消息内容: {send_message}\n" \
                             f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            # 发送通知到各个渠道
            for notification in notifications:
                if not notification.get('enabled', True):
                    continue

                channel_type = notification.get('channel_type')
                channel_config = notification.get('channel_config')

                try:
                    # 解析配置数据
                    config_data = self._parse_notification_config(channel_config)

                    match channel_type:
                        case 'qq':
                            await self._send_qq_notification(config_data, notification_msg)
                        case 'ding_talk' | 'dingtalk':
                            await self._send_dingtalk_notification(config_data, notification_msg)
                        case 'email':
                            await self._send_email_notification(config_data, notification_msg)
                        case 'webhook':
                            await self._send_webhook_notification(config_data, notification_msg)
                        case 'wechat':
                            await self._send_wechat_notification(config_data, notification_msg)
                        case 'telegram':
                            await self._send_telegram_notification(config_data, notification_msg)
                        case _:
                            logger.warning(f"不支持的通知渠道类型: {channel_type}")

                except Exception as notify_error:
                    logger.error(f"发送通知失败 ({notification.get('channel_name', 'Unknown')}): {safe_str(notify_error)}")

        except Exception as e:
            logger.error(f"处理消息通知失败: {safe_str(e)}")

    def _is_normal_token_expiry(self, error_message: str) -> bool:
        """检查是否是正常的令牌过期或其他不需要通知的情况"""
        # 不需要发送通知的关键词
        no_notification_keywords = [
            # 正常的令牌过期
            'FAIL_SYS_TOKEN_EXOIRED::令牌过期',
            'FAIL_SYS_TOKEN_EXPIRED::令牌过期',
            'FAIL_SYS_TOKEN_EXOIRED',
            'FAIL_SYS_TOKEN_EXPIRED',
            '令牌过期',
            # Session过期（正常情况）
            'FAIL_SYS_SESSION_EXPIRED::Session过期',
            'FAIL_SYS_SESSION_EXPIRED',
            'Session过期',
            # Token定时刷新失败（会自动重试）
            'Token定时刷新失败，将自动重试',
            'Token定时刷新失败'
        ]

        # 检查错误消息是否包含不需要通知的关键词
        for keyword in no_notification_keywords:
            if keyword in error_message:
                return True

        return False

    async def send_token_refresh_notification(self, error_message: str, notification_type: str = "token_refresh") -> None:
        """发送Token刷新异常通知（带防重复机制）"""
        try:
            # 检查是否是正常的令牌过期，这种情况不需要发送通知
            if self._is_normal_token_expiry(error_message):
                logger.debug(f"检测到正常的令牌过期，跳过通知: {error_message}")
                return

            # 检查是否在冷却期内
            current_time = time.time()
            last_time = self.parent.last_notification_time.get(notification_type, 0)

            if current_time - last_time < self.parent.notification_cooldown:
                logger.debug(f"通知在冷却期内，跳过发送: {notification_type} (距离上次 {int(current_time - last_time)} 秒)")
                return

            from db_manager import db_manager

            # 获取当前账号的通知配置
            notifications = db_manager.get_account_notifications(self.parent.cookie_id)

            if not notifications:
                logger.debug("未配置消息通知，跳过Token刷新通知")
                return

            # 构造通知消息
            notification_msg = f"""🔴 闲鱼账号Token刷新异常

账号ID: {self.parent.cookie_id}
异常时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}
异常信息: {error_message}

请检查账号Cookie是否过期，如有需要请及时更新Cookie配置。"""

            logger.info(f"准备发送Token刷新异常通知: {self.parent.cookie_id}")

            # 发送通知到各个渠道
            notification_sent = False
            for notification in notifications:
                if not notification.get('enabled', True):
                    continue

                channel_type = notification.get('channel_type')
                channel_config = notification.get('channel_config')

                try:
                    # 解析配置数据
                    config_data = self._parse_notification_config(channel_config)

                    match channel_type:
                        case 'qq':
                            await self._send_qq_notification(config_data, notification_msg)
                            notification_sent = True
                        case 'ding_talk' | 'dingtalk':
                            await self._send_dingtalk_notification(config_data, notification_msg)
                            notification_sent = True
                        case 'email':
                            await self._send_email_notification(config_data, notification_msg)
                            notification_sent = True
                        case 'webhook':
                            await self._send_webhook_notification(config_data, notification_msg)
                            notification_sent = True
                        case 'wechat':
                            await self._send_wechat_notification(config_data, notification_msg)
                            notification_sent = True
                        case 'telegram':
                            await self._send_telegram_notification(config_data, notification_msg)
                            notification_sent = True
                        case _:
                            logger.warning(f"不支持的通知渠道类型: {channel_type}")

                except Exception as notify_error:
                    logger.error(f"发送Token刷新通知失败 ({notification.get('channel_name', 'Unknown')}): {safe_str(notify_error)}")

            # 如果成功发送了通知，更新最后发送时间
            if notification_sent:
                self.parent.last_notification_time[notification_type] = current_time
                logger.info(f"Token刷新通知已发送，下次可发送时间: {time.strftime('%H:%M:%S', time.localtime(current_time + self.parent.notification_cooldown))}")

        except Exception as e:
            logger.error(f"处理Token刷新通知失败: {safe_str(e)}")

    async def send_delivery_failure_notification(self, send_user_name: str, send_user_id: str, item_id: str, error_message: str) -> None:
        """发送自动发货失败通知"""
        try:
            from db_manager import db_manager

            # 获取当前账号的通知配置
            notifications = db_manager.get_account_notifications(self.parent.cookie_id)

            if not notifications:
                logger.debug("未配置消息通知，跳过自动发货通知")
                return

            # 构造通知消息
            notification_message = f"🚨 自动发货通知\n\n" \
                                 f"账号: {self.parent.cookie_id}\n" \
                                 f"买家: {send_user_name} (ID: {send_user_id})\n" \
                                 f"商品ID: {item_id}\n" \
                                 f"结果: {error_message}\n" \
                                 f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n" \
                                 f"请及时处理！"

            # 发送通知到所有已启用的通知渠道
            for notification in notifications:
                if notification.get('enabled', False):
                    channel_type = notification.get('channel_type', 'qq')
                    channel_config = notification.get('channel_config', '')

                    try:
                        # 解析配置数据
                        config_data = self._parse_notification_config(channel_config)

                        match channel_type:
                            case 'qq':
                                await self._send_qq_notification(config_data, notification_message)
                                logger.info(f"已发送自动发货通知到QQ")
                            case 'ding_talk' | 'dingtalk':
                                await self._send_dingtalk_notification(config_data, notification_message)
                                logger.info(f"已发送自动发货通知到钉钉")
                            case 'email':
                                await self._send_email_notification(config_data, notification_message)
                                logger.info(f"已发送自动发货通知到邮箱")
                            case 'webhook':
                                await self._send_webhook_notification(config_data, notification_message)
                                logger.info(f"已发送自动发货通知到Webhook")
                            case 'wechat':
                                await self._send_wechat_notification(config_data, notification_message)
                                logger.info(f"已发送自动发货通知到微信")
                            case 'telegram':
                                await self._send_telegram_notification(config_data, notification_message)
                                logger.info(f"已发送自动发货通知到Telegram")
                            case _:
                                logger.warning(f"不支持的通知渠道类型: {channel_type}")

                    except Exception as notify_error:
                        logger.error(f"发送自动发货通知失败: {safe_str(notify_error)}")

        except Exception as e:
            logger.error(f"发送自动发货通知异常: {safe_str(e)}")
