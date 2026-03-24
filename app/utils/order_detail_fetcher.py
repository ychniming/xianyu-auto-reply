"""
闲鱼订单详情获取工具
基于Playwright实现订单详情页面访问和数据提取
"""

import asyncio
import time
import sys
import os
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from app.utils.browser_config import get_browser_args, USER_AGENT, TIMEOUT_PAGE_LOAD_MS

if sys.platform.startswith('linux') or os.getenv('DOCKER_ENV'):
    try:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    except Exception as e:
        logger.warning(f"Failed to set event loop policy: {e}")

if os.getenv('DOCKER_ENV'):
    try:
        if hasattr(asyncio, 'SelectorEventLoop'):
            loop = asyncio.SelectorEventLoop()
            asyncio.set_event_loop(loop)
    except Exception as e:
        logger.warning(f"Failed to set SelectorEventLoop: {e}")


class OrderDetailFetcher:
    """Xianyu order detail fetcher."""

    def __init__(self, cookie_string: str = None):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,ru;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }

        self.cookie = cookie_string

    async def init_browser(self, headless: bool = True):
        """Initialize browser."""
        try:
            playwright = await async_playwright().start()

            browser_args = get_browser_args()

            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=browser_args
            )

            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=USER_AGENT
            )

            await self.context.set_extra_http_headers(self.headers)

            self.page = await self.context.new_page()

            await self._set_cookies()

            logger.info("Browser initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Browser initialization failed: {e}")
            return False

    async def _set_cookies(self):
        """Set cookies."""
        try:
            cookies = []
            for cookie_pair in self.cookie.split('; '):
                if '=' in cookie_pair:
                    name, value = cookie_pair.split('=', 1)
                    cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.goofish.com',
                        'path': '/'
                    })

            await self.context.add_cookies(cookies)
            logger.info(f"Set {len(cookies)} cookies")

        except Exception as e:
            logger.error(f"Set cookies failed: {e}")

    async def fetch_order_detail(self, order_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Fetch order detail.

        Args:
            order_id: Order ID
            timeout: Timeout in seconds

        Returns:
            Dict with order details or None on failure
        """
        try:
            if not self.page:
                logger.error("Browser not initialized")
                return None

            url = f"https://www.goofish.com/order-detail?orderId={order_id}&role=seller"
            logger.info(f"Accessing order detail page: {url}")

            response = await self.page.goto(url, wait_until='networkidle', timeout=timeout * 1000)

            if not response or response.status != 200:
                logger.error(f"Page access failed, status: {response.status if response else 'None'}")
                return None
            
            logger.info("页面加载成功，等待内容渲染...")
            
            # 等待页面完全加载
            await self.page.wait_for_load_state('networkidle')
            
            # 额外等待确保动态内容加载完成
            await asyncio.sleep(3)
            
            # 获取并解析SKU信息
            sku_info = await self._get_sku_content()

            # 获取页面标题
            title = await self.page.title()

            result = {
                'order_id': order_id,
                'url': url,
                'title': title,
                'sku_info': sku_info,  # 包含解析后的规格信息
                'spec_name': sku_info.get('spec_name', '') if sku_info else '',
                'spec_value': sku_info.get('spec_value', '') if sku_info else '',
                'timestamp': time.time()
            }

            logger.info(f"订单详情获取成功: {order_id}")
            if sku_info:
                logger.info(f"规格信息 - 名称: {result['spec_name']}, 值: {result['spec_value']}")
            return result
            
        except Exception as e:
            logger.error(f"获取订单详情失败: {e}")
            return None

    def _parse_sku_content(self, sku_content: str) -> Dict[str, str]:
        """
        解析SKU内容，根据冒号分割规格名称和规格值

        Args:
            sku_content: 原始SKU内容字符串

        Returns:
            包含规格名称和规格值的字典，如果解析失败则返回空字典
        """
        try:
            if not sku_content or ':' not in sku_content:
                logger.warning(f"SKU内容格式无效或不包含冒号: {sku_content}")
                return {}

            # 根据冒号分割
            parts = sku_content.split(':', 1)  # 只分割第一个冒号

            if len(parts) == 2:
                spec_name = parts[0].strip()
                spec_value = parts[1].strip()

                if spec_name and spec_value:
                    result = {
                        'spec_name': spec_name,
                        'spec_value': spec_value
                    }
                    logger.info(f"SKU解析成功 - 规格名称: {spec_name}, 规格值: {spec_value}")
                    return result
                else:
                    logger.warning(f"SKU解析失败，规格名称或值为空: 名称='{spec_name}', 值='{spec_value}'")
                    return {}
            else:
                logger.warning(f"SKU内容分割失败: {sku_content}")
                return {}

        except Exception as e:
            logger.error(f"解析SKU内容异常: {e}")
            return {}

    async def _get_sku_content(self) -> Optional[Dict[str, str]]:
        """获取并解析SKU内容"""
        try:
            # 等待SKU元素出现
            sku_selector = '.sku--u_ddZval'

            # 检查元素是否存在
            sku_element = await self.page.query_selector(sku_selector)

            if sku_element:
                # 获取元素文本内容
                sku_content = await sku_element.text_content()
                if sku_content:
                    sku_content = sku_content.strip()
                    logger.info(f"找到SKU原始内容: {sku_content}")
                    print(f"🛍️ SKU原始内容: {sku_content}")

                    # 解析SKU内容
                    parsed_sku = self._parse_sku_content(sku_content)
                    if parsed_sku:
                        print(f"📋 规格名称: {parsed_sku['spec_name']}")
                        print(f"📝 规格值: {parsed_sku['spec_value']}")
                        return parsed_sku
                    else:
                        logger.warning("SKU内容解析失败")
                        return {}
                else:
                    logger.warning("SKU元素内容为空")
                    return {}
            else:
                logger.warning("未找到SKU元素")

                # 尝试获取页面的所有class包含sku的元素
                all_sku_elements = await self.page.query_selector_all('[class*="sku"]')
                if all_sku_elements:
                    logger.info(f"找到 {len(all_sku_elements)} 个包含'sku'的元素")
                    for i, element in enumerate(all_sku_elements):
                        class_name = await element.get_attribute('class')
                        text_content = await element.text_content()
                        logger.info(f"SKU元素 {i+1}: class='{class_name}', text='{text_content}'")

                return {}

        except Exception as e:
            logger.error(f"获取SKU内容失败: {e}")
            return {}

    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 便捷函数
async def fetch_order_detail_simple(order_id: str, cookie_string: str = None, headless: bool = True) -> Optional[Dict[str, Any]]:
    """
    简单的订单详情获取函数

    Args:
        order_id: 订单ID
        cookie_string: Cookie字符串，如果不提供则使用默认值
        headless: 是否无头模式

    Returns:
        订单详情字典或None
    """
    fetcher = OrderDetailFetcher(cookie_string)
    try:
        if await fetcher.init_browser(headless=headless):
            return await fetcher.fetch_order_detail(order_id)
    finally:
        await fetcher.close()
    return None


# 测试代码
if __name__ == "__main__":
    async def test():
        # 测试订单ID
        test_order_id = "2856024697612814489"
        
        print(f"🔍 开始获取订单详情: {test_order_id}")
        
        result = await fetch_order_detail_simple(test_order_id, headless=False)
        
        if result:
            print("✅ 订单详情获取成功:")
            print(f"📋 订单ID: {result['order_id']}")
            print(f"🌐 URL: {result['url']}")
            print(f"📄 页面标题: {result['title']}")
            print(f"🛍️ SKU内容: {result['sku_content']}")
        else:
            print("❌ 订单详情获取失败")
    
    # 运行测试
    asyncio.run(test())
