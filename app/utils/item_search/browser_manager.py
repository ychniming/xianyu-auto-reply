"""
Xianyu Item Search Module - Browser Management
Handles Playwright browser initialization, configuration and cleanup.
"""

import sys
import os
import asyncio
from typing import Optional
from loguru import logger

from app.utils.browser_config import get_browser_args, USER_AGENT, TIMEOUT_PAGE_LOAD_MS, TIMEOUT_NETWORK_IDLE_MS, TIMEOUT_NETWORK_IDLE_LONG_MS

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

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = None
    BrowserContext = None
    Page = None
    logger.warning("Playwright not installed, real search unavailable")


class BrowserManager:
    """Browser manager for Playwright lifecycle management."""

    def __init__(self):
        """Initialize browser manager."""
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None

    @property
    def is_available(self) -> bool:
        """Check if Playwright is available.

        Returns:
            bool: True if Playwright is available
        """
        return PLAYWRIGHT_AVAILABLE

    @property
    def is_initialized(self) -> bool:
        """Check if browser is initialized.

        Returns:
            bool: True if browser is initialized
        """
        return self.browser is not None and self.page is not None

    def _get_browser_args(self) -> list:
        """Get browser launch arguments.

        Returns:
            list: Browser launch arguments
        """
        return get_browser_args()

    async def init_browser(self) -> None:
        """Initialize browser.

        Raises:
            Exception: Raised when Playwright is not installed
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise Exception("Playwright not installed, real search unavailable")

        if not self.browser:
            self._playwright = await async_playwright().start()
            logger.info("Starting browser...")

            browser_args = self._get_browser_args()

            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=browser_args
            )
            self.context = await self.browser.new_context(
                user_agent=USER_AGENT
            )
            self.page = await self.context.new_page()
            logger.info("Browser started successfully")

    async def close_browser(self) -> None:
        """Close browser and release resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
            logger.info("Browser closed")

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def navigate(self, url: str, timeout: int = TIMEOUT_PAGE_LOAD_MS) -> bool:
        """Navigate to specified URL.

        Args:
            url: Target URL
            timeout: Timeout in milliseconds

        Returns:
            bool: True if navigation succeeded
        """
        if not self.page:
            logger.error("Browser page not initialized")
            return False

        try:
            await self.page.goto(url, timeout=timeout)
            await self.page.wait_for_load_state("networkidle", timeout=TIMEOUT_NETWORK_IDLE_MS)
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            return False

    async def fill_input(self, selector: str, value: str) -> bool:
        """Fill input field.

        Args:
            selector: CSS selector
            value: Value to fill

        Returns:
            bool: True if fill succeeded
        """
        if not self.page:
            logger.error("Browser page not initialized")
            return False

        try:
            await self.page.fill(selector, value)
            return True
        except Exception as e:
            logger.error(f"Fill input failed: {str(e)}")
            return False

    async def click(self, selector: str) -> bool:
        """Click element.

        Args:
            selector: CSS selector

        Returns:
            bool: True if click succeeded
        """
        if not self.page:
            logger.error("Browser page not initialized")
            return False

        try:
            await self.page.click(selector)
            return True
        except Exception as e:
            logger.error(f"Click element failed: {str(e)}")
            return False

    async def wait_for_load(self, timeout: int = TIMEOUT_NETWORK_IDLE_LONG_MS) -> None:
        """Wait for page to load.

        Args:
            timeout: Timeout in milliseconds
        """
        if self.page:
            try:
                await self.page.wait_for_load_state("networkidle", timeout=timeout)
            except Exception as e:
                logger.warning(f"Wait for load timeout: {str(e)}")

    async def press_key(self, key: str) -> None:
        """Press key.

        Args:
            key: Key name
        """
        if self.page:
            try:
                await self.page.keyboard.press(key)
            except Exception as e:
                logger.warning(f"Key press failed: {str(e)}")

    def on_response(self, callback) -> None:
        """Register response listener.

        Args:
            callback: Callback function
        """
        if self.page:
            self.page.on("response", callback)
