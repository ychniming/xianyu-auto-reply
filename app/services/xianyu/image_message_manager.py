"""
闲鱼自动回复系统 - 图片消息管理模块
负责图片消息的发送和上传功能
"""

import os
import json
import base64
from typing import Optional
from loguru import logger

from app.utils.xianyu_utils import generate_mid, generate_uuid
from app.services.xianyu.common import safe_str


class ImageMessageManager:
    """图片消息管理器 - 负责图片消息的发送和上传"""

    def __init__(self, parent):
        """初始化图片消息管理器

        Args:
            parent: XianyuLive实例，用于访问共享属性
        """
        self.parent = parent

    async def send_image_msg(self, ws, cid: str, toid: str, image_url: str, width: int = 800, height: int = 600, card_id: int = None) -> None:
        """发送图片消息"""
        try:
            original_url = image_url

            if self.parent._is_cdn_url(image_url):
                logger.info(f"【{self.parent.cookie_id}】使用已有的CDN图片链接: {image_url}")
            elif image_url.startswith('/static/uploads/') or image_url.startswith('static/uploads/'):
                local_image_path = image_url.replace('/static/uploads/', 'static/uploads/')
                if os.path.exists(local_image_path):
                    logger.info(f"【{self.parent.cookie_id}】准备上传本地图片到闲鱼CDN: {local_image_path}")

                    from app.utils.image_uploader import ImageUploader
                    uploader = ImageUploader(self.parent.cookies_str)

                    async with uploader:
                        cdn_url = await uploader.upload_image(local_image_path)
                        if cdn_url:
                            logger.info(f"【{self.parent.cookie_id}】图片上传成功，CDN URL: {cdn_url}")
                            image_url = cdn_url

                            if card_id is not None:
                                await self.parent._update_card_image_url(card_id, cdn_url)

                            from app.utils.image_utils import image_manager
                            try:
                                actual_width, actual_height = image_manager.get_image_size(local_image_path)
                                if actual_width and actual_height:
                                    width, height = actual_width, actual_height
                                    logger.info(f"【{self.parent.cookie_id}】获取到实际图片尺寸: {width}x{height}")
                            except Exception as e:
                                logger.warning(f"【{self.parent.cookie_id}】获取图片尺寸失败，使用默认尺寸: {e}")
                        else:
                            logger.error(f"【{self.parent.cookie_id}】图片上传失败: {local_image_path}")
                            raise Exception(f"图片上传失败: {local_image_path}")
                else:
                    logger.error(f"【{self.parent.cookie_id}】本地图片文件不存在: {local_image_path}")
                    raise Exception(f"本地图片文件不存在: {local_image_path}")
            else:
                logger.warning(f"【{self.parent.cookie_id}】未知的图片URL格式: {image_url}")

            logger.info(f"【{self.parent.cookie_id}】准备发送图片消息:")
            logger.info(f"  - 原始URL: {original_url}")
            logger.info(f"  - CDN URL: {image_url}")
            logger.info(f"  - 图片尺寸: {width}x{height}")
            logger.info(f"  - 聊天ID: {cid}")
            logger.info(f"  - 接收者ID: {toid}")

            image_content = {
                "contentType": 2,
                "image": {
                    "pics": [{
                        "height": int(height),
                        "type": 0,
                        "url": image_url,
                        "width": int(width)
                    }]
                }
            }

            content_json = json.dumps(image_content, ensure_ascii=False)
            content_base64 = str(base64.b64encode(content_json.encode('utf-8')), 'utf-8')

            logger.info(f"【{self.parent.cookie_id}】图片内容JSON: {content_json}")
            logger.info(f"【{self.parent.cookie_id}】Base64编码长度: {len(content_base64)}")

            msg = {
                "lwp": "/r/MessageSend/sendByReceiverScope",
                "headers": {"mid": generate_mid()},
                "body": [
                    {
                        "uuid": generate_uuid(),
                        "cid": f"{cid}@goofish",
                        "conversationType": 1,
                        "content": {
                            "contentType": 101,
                            "custom": {"type": 1, "data": content_base64}
                        },
                        "redPointPolicy": 0,
                        "extension": {"extJson": "{}"},
                        "ctx": {"appVersion": "1.0", "platform": "web"},
                        "mtags": {},
                        "msgReadStatusSetting": 1
                    },
                    {
                        "actualReceivers": [f"{toid}@goofish", f"{self.parent.myid}@goofish"]
                    }
                ]
            }

            await ws.send(json.dumps(msg))
            logger.info(f"【{self.parent.cookie_id}】图片消息发送成功: {image_url}")

        except Exception as e:
            logger.error(f"【{self.parent.cookie_id}】发送图片消息失败: {safe_str(e)}")
            raise

    async def send_image_from_file(self, ws, cid: str, toid: str, image_path: str) -> bool:
        """从本地文件发送图片"""
        try:
            logger.info(f"【{self.parent.cookie_id}】开始上传图片: {image_path}")

            from app.utils.image_uploader import ImageUploader
            uploader = ImageUploader(self.parent.cookies_str)

            async with uploader:
                image_url = await uploader.upload_image(image_path)

            if image_url:
                from app.utils.image_utils import image_manager
                try:
                    from PIL import Image
                    with Image.open(image_path) as img:
                        width, height = img.size
                except Exception as e:
                    logger.warning(f"无法获取图片尺寸，使用默认值: {e}")
                    width, height = 800, 600

                await self.send_image_msg(ws, cid, toid, image_url, width, height)
                logger.info(f"【{self.parent.cookie_id}】图片发送完成: {image_path} -> {image_url}")
                return True
            else:
                logger.error(f"【{self.parent.cookie_id}】图片上传失败: {image_path}")
                return False

        except Exception as e:
            logger.error(f"【{self.parent.cookie_id}】从文件发送图片失败: {safe_str(e)}")
            return False
