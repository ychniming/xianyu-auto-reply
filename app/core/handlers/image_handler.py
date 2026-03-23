"""
图片处理模块

提供图片URL处理、上传、CDN管理等功能
"""

import os
from typing import Optional, Tuple

from loguru import logger

from app.core.constants import (
    CDN_DOMAINS,
    IMAGE_EXTENSIONS,
)


class ImageHandler:
    """图片处理器

    从XianyuAutoAsync中提取的图片处理逻辑，提供图片URL验证、
    CDN链接处理和本地上传功能。

    Attributes:
        cookie_id: 账号ID
        cookies_str: Cookie字符串
    """

    def __init__(self, cookie_id: str, cookies_str: str) -> None:
        """初始化图片处理器

        Args:
            cookie_id: 账号ID
            cookies_str: Cookie字符串
        """
        self.cookie_id: str = cookie_id
        self.cookies_str: str = cookies_str

    @staticmethod
    def is_cdn_url(url: str) -> bool:
        """检查URL是否是闲鱼CDN链接

        Args:
            url: 图片URL

        Returns:
            bool: 是否为CDN链接
        """
        if not url:
            return False

        url_lower = url.lower()
        for domain in CDN_DOMAINS:
            if domain in url_lower:
                return True

        if url_lower.startswith("https://") and any(ext in url_lower for ext in IMAGE_EXTENSIONS):
            return True

        return False

    async def handle_image_keyword(self, keyword: str, image_url: str) -> str:
        """处理图片类型关键词，返回图片发送指令或错误消息

        Args:
            keyword: 关键词
            image_url: 图片URL

        Returns:
            str: 图片发送指令或错误消息
        """
        try:
            if self.is_cdn_url(image_url):
                logger.info(f"[{self.cookie_id}] 使用已有的CDN图片链接: {image_url}")
                return f"__IMAGE_SEND__{image_url}"

            elif image_url.startswith("/static/uploads/") or image_url.startswith("static/uploads/"):
                local_image_path = image_url.replace("/static/uploads/", "static/uploads/")
                if os.path.exists(local_image_path):
                    logger.info(f"[{self.cookie_id}] 准备上传本地图片到闲鱼CDN: {local_image_path}")

                    from app.utils.image_uploader import ImageUploader
                    uploader = ImageUploader(self.cookies_str)

                    async with uploader:
                        cdn_url = await uploader.upload_image(local_image_path)
                        if cdn_url:
                            logger.info(f"[{self.cookie_id}] 图片上传成功，CDN URL: {cdn_url}")
                            await self.update_keyword_image_url(keyword, cdn_url)
                            return f"__IMAGE_SEND__{cdn_url}"
                        else:
                            logger.error(f"[{self.cookie_id}] 图片上传失败: {local_image_path}")
                            return "抱歉，图片发送失败，请稍后重试。"
                else:
                    logger.error(f"[{self.cookie_id}] 本地图片文件不存在: {local_image_path}")
                    return "抱歉，图片文件不存在。"

            else:
                logger.info(f"[{self.cookie_id}] 使用外部图片链接: {image_url}")
                return f"__IMAGE_SEND__{image_url}"

        except Exception as e:
            logger.error(f"[{self.cookie_id}] 处理图片关键词失败: {e}")
            return f"抱歉，图片发送失败: {str(e)}"

    async def update_keyword_image_url(self, keyword: str, new_image_url: str) -> bool:
        """更新关键词的图片URL

        Args:
            keyword: 关键词
            new_image_url: 新的图片URL

        Returns:
            bool: 更新是否成功
        """
        try:
            from app.repositories import db_manager
            success = db_manager.update_keyword_image_url(self.cookie_id, keyword, new_image_url)
            if success:
                logger.info(f"[{self.cookie_id}] 图片URL已更新: {keyword} -> {new_image_url}")
            else:
                logger.warning(f"[{self.cookie_id}] 图片URL更新失败: {keyword}")
            return success
        except Exception as e:
            logger.error(f"[{self.cookie_id}] 更新关键词图片URL失败: {e}")
            return False

    async def update_card_image_url(self, card_id: int, new_image_url: str) -> bool:
        """更新卡券的图片URL

        Args:
            card_id: 卡券ID
            new_image_url: 新的图片URL

        Returns:
            bool: 更新是否成功
        """
        try:
            from app.repositories import db_manager
            success = db_manager.update_card_image_url(card_id, new_image_url)
            if success:
                logger.info(f"[{self.cookie_id}] 卡券图片URL已更新: 卡券ID={card_id} -> {new_image_url}")
            else:
                logger.warning(f"[{self.cookie_id}] 卡券图片URL更新失败: 卡券ID={card_id}")
            return success
        except Exception as e:
            logger.error(f"[{self.cookie_id}] 更新卡券图片URL失败: {e}")
            return False

    async def prepare_image_for_send(
        self, image_url: str, card_id: Optional[int] = None
    ) -> Tuple[str, Optional[Tuple[int, int]]]:
        """准备图片用于发送

        Args:
            image_url: 原始图片URL
            card_id: 可选的卡券ID，用于更新卡券图片URL

        Returns:
            Tuple[str, Optional[Tuple[int, int]]]: (处理后的URL, 图片尺寸(width, height)或None)
        """
        try:
            if self.is_cdn_url(image_url):
                logger.info(f"[{self.cookie_id}] 使用已有的CDN图片链接: {image_url}")
                return image_url, None

            elif image_url.startswith("/static/uploads/") or image_url.startswith("static/uploads/"):
                local_image_path = image_url.replace("/static/uploads/", "static/uploads/")
                if os.path.exists(local_image_path):
                    logger.info(f"[{self.cookie_id}] 准备上传本地图片到闲鱼CDN: {local_image_path}")

                    from app.utils.image_uploader import ImageUploader
                    uploader = ImageUploader(self.cookies_str)

                    async with uploader:
                        cdn_url = await uploader.upload_image(local_image_path)
                        if cdn_url:
                            logger.info(f"[{self.cookie_id}] 图片上传成功: {cdn_url}")

                            if card_id:
                                await self.update_card_image_url(card_id, cdn_url)

                            from app.utils.image_utils import image_manager
                            size: Optional[Tuple[int, int]] = None
                            if hasattr(image_manager, "get_image_size"):
                                try:
                                    actual_width, actual_height = image_manager.get_image_size(local_image_path)
                                    size = (actual_width, actual_height)
                                except Exception as e:
                                    logger.warning(f"[{self.cookie_id}] 获取图片尺寸失败: {e}")

                            return cdn_url, size
                        else:
                            raise Exception(f"图片上传失败: {local_image_path}")
                else:
                    raise Exception(f"本地图片文件不存在: {local_image_path}")

            else:
                logger.warning(f"[{self.cookie_id}] 未知的图片URL格式: {image_url}")
                return image_url, None

        except Exception as e:
            logger.error(f"[{self.cookie_id}] 图片准备失败: {e}")
            raise


image_handler = ImageHandler
