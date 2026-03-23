"""
QQ 开放平台 WebSocket 客户端
用于获取用户 OpenID

使用方法：
1. 启动服务，连接到 QQ 开放平台 WebSocket
2. 给机器人发送消息
3. 从消息事件中提取用户的 OpenID
"""

import asyncio
import json
import time
from typing import Optional, Dict, List
from loguru import logger


class QQBotWebSocketClient:
    """QQ 开放平台 WebSocket 客户端"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token: Optional[str] = None
        self.ws = None
        self._running = False
        self.openid_cache: Dict[str, dict] = {}

    async def get_access_token(self) -> Optional[str]:
        """获取 Access Token"""
        if self.access_token:
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
                    logger.info("QQ机器人 Access Token 获取成功")
                    return self.access_token
                else:
                    error_text = await response.text()
                    logger.error(f"获取 Access Token 失败: {error_text}")
                    return None

    async def connect(self) -> bool:
        """连接 WebSocket"""
        import websockets
        import aiohttp
        
        if not self.access_token:
            await self.get_access_token()

        if not self.access_token:
            logger.error("无法获取 Access Token")
            return False

        # 先通过 HTTP API 获取 WebSocket Gateway URL
        gateway_url = "https://sandbox.api.sgroup.qq.com/gateway"
        headers = {
            "Authorization": f"QQBot {self.access_token}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(gateway_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        ws_url = result.get('url')
                        logger.info(f"获取到 WebSocket URL: {ws_url}")
                    else:
                        error_text = await response.text()
                        logger.error(f"获取 Gateway URL 失败: {response.status} - {error_text}")
                        return False

            # 连接 WebSocket
            self.ws = await websockets.connect(ws_url)
            logger.info("已连接到 QQ 开放平台 WebSocket")

            # 发送鉴权
            auth_data = {
                "op": 2,
                "d": {
                    "token": f"QQBot {self.access_token}",
                    "intents": 33554432,  # C2C_MESSAGE事件
                    "shard": [0, 1],
                    "properties": {
                        "$os": "windows",
                        "$browser": "chrome",
                        "$device": "pc"
                    }
                }
            }
            await self.ws.send(json.dumps(auth_data))
            logger.info("已发送鉴权请求")

            self._running = True

            # 启动心跳任务
            asyncio.create_task(self._heartbeat())

            # 监听消息
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    logger.debug(f"收到消息: {json.dumps(data, ensure_ascii=False)}")

                    # 处理事件
                    op = data.get('op')
                    event_type = data.get('t')
                    
                    if op == 10:  # Hello
                        heartbeat_interval = data.get('d', {}).get('heartbeat_interval', 45000)
                        logger.info(f"收到 Hello，心跳间隔: {heartbeat_interval}ms")
                    elif event_type == 'READY':
                        logger.info("✅ WebSocket 连接就绪")
                    elif event_type == 'C2C_MESSAGE_CREATE':
                        openid = data.get('d', {}).get('author', {}).get('user_openid')
                        if openid:
                            logger.info(f"🎉 捕获到用户 OpenID: {openid}")
                            self._save_openid(openid)
                    elif event_type == 'C2C_MSG_RECEIVE':
                        openid = data.get('d', {}).get('author', {}).get('user_openid')
                        if openid:
                            logger.info(f"收到私聊消息，OpenID: {openid}")
                except Exception as e:
                    logger.error(f"处理消息错误: {e}")

            self._running = False
            return True

        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    async def _heartbeat(self):
        """发送心跳包"""
        while self._running:
            try:
                await asyncio.sleep(30)
                if self.ws:
                    await self.ws.send(json.dumps({"op": 11}))
                    logger.debug("心跳包已发送")
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                self._running = False

    def _save_openid(self, openid: str):
        """保存 OpenID 到文件"""
        try:
            self.openid_cache[openid] = {
                'openid': openid,
                'timestamp': time.time()
            }
            
            with open('openid_cache.txt', 'a', encoding='utf-8') as f:
                f.write(f"{openid}\n")
            
            logger.info(f"保存新的 OpenID: {openid}")
        except Exception as e:
            logger.error(f"保存 OpenID 失败: {e}")

    def get_cached_openids(self) -> List[str]:
        """获取所有缓存的 OpenID"""
        return list(self.openid_cache.keys())

    async def stop(self):
        """停止 WebSocket 连接"""
        self._running = False
        if self.ws:
            await self.ws.close()
            logger.info("WebSocket 连接已关闭")


async def main():
    """主函数"""
    # 配置信息
    app_id = "102891558"
    app_secret = "rS3fHuXBpT8nT9qXFxgP9tdO9vhUH5ti"

    client = QQBotWebSocketClient(app_id, app_secret)

    print("=" * 60)
    print("QQ 开放平台 WebSocket 客户端")
    print("=" * 60)
    print(f"AppID: {app_id}")
    print(f"AppSecret: {app_secret[:10]}...")
    print()
    print("正在启动...")
    print("提示：请先在 QQ 开放平台后台添加沙箱成员")
    print("然后用你的 QQ 给机器人发送消息")
    print("系统会自动捕获 OpenID 并保存")
    print()
    print("按 Ctrl+C 停止监听")
    print("=" * 60)

    try:
        await client.connect()
    except KeyboardInterrupt:
        print("\n停止监听")
        await client.stop()
        print("\n捕获的 OpenID:")
        for openid in client.get_cached_openids():
            print(f"  OpenID: {openid}")


if __name__ == "__main__":
    asyncio.run(main())
