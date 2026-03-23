"""
QQ 开放平台 WebSocket 客户端
用于监听消息事件并获取用户 OpenID
"""

import asyncio
import json
import time
from typing import Optional, Callable, Dict, Any
from loguru import logger


class QQBotWebSocketClient:
    """QQ 开放平台 WebSocket 客户端"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.ws: Optional[Any] = None
        self.is_running: bool = False
        self.on_message_callback: Optional[Callable] = None
        self.openid_cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_access_token(self) -> str:
        """获取 Access Token"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        import aiohttp
        
        url = "https://bots.qq.com/app/getAppAccessToken"
        data = {
            "appId": self.app_id,
            "clientSecret": self.app_secret
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result.get('access_token')
                    expires_in_str = result.get('expires_in', '7200')
                    
                    try:
                        expires_in = int(expires_in_str)
                    except (ValueError, TypeError):
                        expires_in = 7200
                    
                    self.token_expires_at = time.time() + expires_in - 300
                    logger.info(f"QQ机器人 Access Token 获取成功，有效期 {expires_in} 秒")
                    return self.access_token
                else:
                    error_text = await response.text()
                    raise Exception(f"获取 Token 失败：{response.status} - {error_text}")
    
    async def get_gateway_url(self) -> str:
        """获取 WebSocket Gateway URL"""
        import aiohttp
        
        if not self.access_token:
            await self.get_access_token()
        
        # 沙箱环境的 Gateway URL
        url = "https://sandbox.api.sgroup.qq.com/gateway"
        headers = {
            "Authorization": f"QQBot {self.access_token}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    gateway_url = result.get('url')
                    logger.info(f"获取 Gateway URL 成功: {gateway_url}")
                    return gateway_url
                else:
                    error_text = await response.text()
                    raise Exception(f"获取 Gateway URL 失败：{response.status} - {error_text}")
    
    async def connect(self):
        """连接到 WebSocket Gateway"""
        import websockets
        
        try:
            gateway_url = await self.get_gateway_url()
            
            logger.info(f"正在连接 WebSocket: {gateway_url}")
            self.ws = await websockets.connect(gateway_url)
            self.is_running = True
            
            logger.info("WebSocket 连接成功")
            
            # 发送心跳
            await self._send_heartbeat()
            
            # 开始监听消息
            await self._listen()
            
        except Exception as e:
            logger.error(f"WebSocket 连接失败: {e}")
            self.is_running = False
            raise
    
    async def _send_heartbeat(self):
        """发送心跳包"""
        if not self.ws:
            return
        
        try:
            heartbeat = {
                "op": 1,
                "d": int(time.time())
            }
            await self.ws.send(json.dumps(heartbeat))
            logger.debug("心跳包已发送")
        except Exception as e:
            logger.error(f"发送心跳失败: {e}")
    
    async def _listen(self):
        """监听 WebSocket 消息"""
        if not self.ws:
            return
        
        logger.info("开始监听 WebSocket 消息...")
        
        while self.is_running:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # 处理不同类型的消息
                op = data.get('op')
                
                if op == 0:  # Dispatch 事件
                    event_type = data.get('t')
                    event_data = data.get('d', {})
                    
                    logger.info(f"收到事件: {event_type}")
                    
                    # 处理单聊消息事件
                    if event_type == 'C2C_MESSAGE_CREATE':
                        await self._handle_c2c_message(event_data)
                    
                    # 处理好友添加事件
                    elif event_type == 'FRIEND_ADD':
                        await self._handle_friend_add(event_data)
                    
                    # 处理群消息事件
                    elif event_type == 'GROUP_AT_MESSAGE_CREATE':
                        await self._handle_group_message(event_data)
                
                elif op == 10:  # Hello 事件
                    # 开始心跳
                    heartbeat_interval = data.get('d', {}).get('heartbeat_interval', 45000)
                    asyncio.create_task(self._heartbeat_loop(heartbeat_interval / 1000))
                
                elif op == 11:  # 心跳 ACK
                    logger.debug("心跳 ACK 收到")
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket 连接已关闭")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"监听消息异常: {e}")
    
    async def _heartbeat_loop(self, interval: float):
        """心跳循环"""
        while self.is_running:
            await asyncio.sleep(interval)
            await self._send_heartbeat()
    
    async def _handle_c2c_message(self, event_data: dict):
        """处理单聊消息事件"""
        try:
            author = event_data.get('author', {})
            openid = author.get('user_openid')
            content = event_data.get('content', {})
            message_content = content.get('content', '')
            
            if openid:
                # 缓存 OpenID
                self.openid_cache[openid] = {
                    'openid': openid,
                    'timestamp': time.time(),
                    'last_message': message_content
                }
                
                logger.info(f"✅ 捕获到 OpenID: {openid}")
                logger.info(f"   消息内容: {message_content}")
                
                # 调用回调函数
                if self.on_message_callback:
                    await self.on_message_callback({
                        'type': 'C2C_MESSAGE_CREATE',
                        'openid': openid,
                        'message': message_content,
                        'event_data': event_data
                    })
                
                # 保存到文件
                await self._save_openid_to_file(openid, event_data)
                
        except Exception as e:
            logger.error(f"处理单聊消息异常: {e}")
    
    async def _handle_friend_add(self, event_data: dict):
        """处理好友添加事件"""
        try:
            openid = event_data.get('user_openid')
            
            if openid:
                logger.info(f"✅ 新好友 OpenID: {openid}")
                
                if self.on_message_callback:
                    await self.on_message_callback({
                        'type': 'FRIEND_ADD',
                        'openid': openid,
                        'event_data': event_data
                    })
                
                await self._save_openid_to_file(openid, event_data)
                
        except Exception as e:
            logger.error(f"处理好友添加异常: {e}")
    
    async def _handle_group_message(self, event_data: dict):
        """处理群消息事件"""
        try:
            author = event_data.get('author', {})
            openid = author.get('member_openid')
            group_openid = event_data.get('group_openid')
            
            if openid:
                logger.info(f"✅ 群消息 OpenID: {openid}, 群: {group_openid}")
                
                if self.on_message_callback:
                    await self.on_message_callback({
                        'type': 'GROUP_MESSAGE',
                        'openid': openid,
                        'group_openid': group_openid,
                        'event_data': event_data
                    })
                
        except Exception as e:
            logger.error(f"处理群消息异常: {e}")
    
    async def _save_openid_to_file(self, openid: str, event_data: dict):
        """保存 OpenID 到文件"""
        try:
            from pathlib import Path
            
            cache_file = Path(__file__).parent.parent / "data" / "qq_openid_cache.json"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取现有数据
            cache_data = {}
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            
            # 更新数据
            cache_data[openid] = {
                'openid': openid,
                'timestamp': time.time(),
                'event_data': event_data
            }
            
            # 保存数据
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"OpenID 已保存到文件: {cache_file}")
            
        except Exception as e:
            logger.error(f"保存 OpenID 失败: {e}")
    
    async def disconnect(self):
        """断开 WebSocket 连接"""
        self.is_running = False
        if self.ws:
            await self.ws.close()
            logger.info("WebSocket 连接已断开")
    
    def set_message_callback(self, callback: Callable):
        """设置消息回调函数"""
        self.on_message_callback = callback
    
    def get_cached_openids(self) -> Dict[str, Dict[str, Any]]:
        """获取缓存的 OpenID 列表"""
        return self.openid_cache.copy()


async def main():
    """主函数 - 测试 WebSocket 客户端"""
    
    # 配置信息
    app_id = "102891558"
    app_secret = "rS3fHuXBpT8nT9qXFxgP9tdO9vhUH5ti"
    
    # 创建客户端
    client = QQBotWebSocketClient(app_id, app_secret)
    
    # 设置消息回调
    async def on_message(data):
        print("\n" + "=" * 60)
        print(f"收到消息事件: {data['type']}")
        print(f"OpenID: {data['openid']}")
        print("=" * 60)
    
    client.set_message_callback(on_message)
    
    print("=" * 60)
    print("QQ 开放平台 WebSocket 客户端")
    print("=" * 60)
    print()
    print(f"AppID: {app_id}")
    print()
    print("正在连接 WebSocket...")
    print()
    print("⚠️ 请用你的 QQ 给机器人发送消息")
    print("   机器人 QQ 号: 3889894364")
    print()
    print("监听中... (按 Ctrl+C 停止)")
    print("-" * 60)
    
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("\n\n正在断开连接...")
        await client.disconnect()
        print("已停止")
    except Exception as e:
        print(f"\n错误: {e}")
        await client.disconnect()


if __name__ == "__main__":
    import websockets
    asyncio.run(main())
