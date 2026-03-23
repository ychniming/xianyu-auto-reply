"""
Browser Configuration Module
Shared browser configuration for Playwright-based modules.
"""

import os
from typing import List


BROWSER_ARGS_BASE = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--no-first-run',
    '--no-zygote',
    '--disable-gpu',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-features=TranslateUI',
    '--disable-ipc-flooding-protection',
    '--disable-extensions',
    '--disable-default-apps',
    '--disable-sync',
    '--disable-translate',
    '--hide-scrollbars',
    '--mute-audio',
    '--no-default-browser-check',
    '--no-pings',
    '--single-process'
]

BROWSER_ARGS_DOCKER = BROWSER_ARGS_BASE + [
    '--disable-background-networking',
    '--disable-background-timer-throttling',
    '--disable-client-side-phishing-detection',
    '--disable-default-apps',
    '--disable-hang-monitor',
    '--disable-popup-blocking',
    '--disable-prompt-on-repost',
    '--disable-sync',
    '--disable-web-resources',
    '--metrics-recording-only',
    '--no-first-run',
    '--safebrowsing-disable-auto-update',
    '--enable-automation',
    '--password-store=basic',
    '--use-mock-keychain'
]


def get_browser_args() -> List[str]:
    """Get browser arguments based on environment.

    Returns:
        List[str]: Browser launch arguments
    """
    if os.getenv('DOCKER_ENV'):
        return BROWSER_ARGS_DOCKER
    return BROWSER_ARGS_BASE


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

TIMEOUT_PAGE_LOAD_MS = 30000
TIMEOUT_NETWORK_IDLE_MS = 10000
TIMEOUT_NETWORK_IDLE_LONG_MS = 15000
TIMEOUT_BUTTON_VISIBLE_MS = 3000
