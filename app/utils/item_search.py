"""
商品搜索模块

提供闲鱼商品搜索功能
"""
from typing import Dict, Any, Optional
from loguru import logger

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed, search will return empty results")


class XianyuSearcher:
    """闲鱼商品搜索器"""

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def search_items(self, keyword: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """搜索闲鱼商品"""
        if not PLAYWRIGHT_AVAILABLE:
            return {
                'items': [],
                'total': 0,
                'error': 'Playwright not available'
            }
        
        return {
            'items': [],
            'total': 0,
            'is_real_data': False,
            'source': 'mock'
        }

    async def search_multiple_pages(self, keyword: str, total_pages: int = 1) -> Dict[str, Any]:
        """搜索多页闲鱼商品"""
        if not PLAYWRIGHT_AVAILABLE:
            return {
                'items': [],
                'total': 0,
                'error': 'Playwright not available'
            }
        
        return {
            'items': [],
            'total': 0,
            'is_real_data': False,
            'source': 'mock'
        }

    async def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None


_searcher: Optional[XianyuSearcher] = None


async def search_xianyu_items(keyword: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """搜索闲鱼商品的便捷函数"""
    global _searcher
    
    if not _searcher:
        _searcher = XianyuSearcher()
    
    try:
        return await _searcher.search_items(keyword, page, page_size)
    except Exception as e:
        logger.error(f"搜索商品失败: {str(e)}")
        return {'items': [], 'total': 0, 'error': str(e)}


async def search_multiple_pages_xianyu(keyword: str, total_pages: int = 1) -> Dict[str, Any]:
    """搜索多页闲鱼商品的便捷函数"""
    global _searcher
    
    if not _searcher:
        _searcher = XianyuSearcher()
    
    try:
        return await _searcher.search_multiple_pages(keyword, total_pages)
    except Exception as e:
        logger.error(f"多页搜索商品失败: {str(e)}")
        return {'items': [], 'total': 0, 'error': str(e)}


async def get_item_detail_from_api(item_id: str) -> Optional[str]:
    """从外部API获取商品详情"""
    try:
        import aiohttp
        
        api_url = f"https://selfapi.zhinianboke.com/api/getItemDetail/{item_id}"
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('status') == '200' and result.get('data'):
                        return result['data']
        
        return None
    except Exception as e:
        logger.error(f"获取商品详情失败: {item_id}, 错误: {str(e)}")
        return None
