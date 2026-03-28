#!/usr/bin/env python3
"""
项目启动入口

主要功能：
1. 创建CookieManager，按配置文件/环境变量初始化账号任务
2. 在后台线程启动FastAPI (reply_server) 提供管理与自动回复接口
3. 主协程保持运行
"""

import os
import sys
import asyncio
import threading
import time
import uvicorn
from urllib.parse import urlparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from configs.config import AUTO_REPLY, COOKIES_LIST


def _start_api_server():
    """启动API服务器"""
    api_conf = AUTO_REPLY.get('api', {})
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '9000'))
    
    if 'host' in api_conf:
        host = api_conf['host']
    if 'port' in api_conf:
        port = api_conf['port']
    
    if 'url' in api_conf and 'host' not in api_conf and 'port' not in api_conf:
        url = api_conf.get('url', 'http://0.0.0.0:9000/xianyu/reply')
        parsed = urlparse(url)
        if parsed.hostname and parsed.hostname != 'localhost':
            host = parsed.hostname
        port = parsed.port or 9000
    
    logger.info(f"启动Web服务器: http://{host}:{port}")
    
    from app.api import app
    uvicorn.run(app, host=host, port=port, log_level="info")


def _setup_keyword_matcher_callbacks(cookie_manager):
    """设置关键词匹配器回调函数"""
    try:
        from app.core.keyword_matcher import keyword_matcher
        from app.repositories import db_manager
        
        def update_sequence_index(cookie_id, keyword, new_index):
            db_manager.update_keyword_sequence_index(cookie_id, keyword, new_index)
        
        def update_trigger_count(cookie_id, keyword, count):
            db_manager.update_keyword_trigger_count(cookie_id, keyword, count)
        
        keyword_matcher.set_sequence_index_updater(update_sequence_index)
        keyword_matcher.set_trigger_count_updater(update_trigger_count)
        
        logger.info("关键词匹配器回调函数设置完成")
    except ImportError as e:
        logger.warning(f"关键词匹配器回调设置失败: {e}")


def _init_keyword_matcher(cookie_manager):
    """初始化关键词匹配器"""
    try:
        from app.core.keyword_matcher import keyword_matcher
        
        all_keywords = []
        for cookie_id in cookie_manager.cookies.keys():
            keywords = db_manager.get_keywords(cookie_id)
            for kw in keywords:
                all_keywords.append({
                    'cookie_id': cookie_id,
                    'keyword': kw[0],
                    'reply': kw[1]
                })
        
        if all_keywords:
            keyword_matcher.load_keywords(all_keywords)
            logger.info(f"已加载 {len(all_keywords)} 个关键词到匹配器")
        else:
            logger.info("没有关键词数据，跳过关键词匹配器初始化")
    except ImportError as e:
        logger.warning(f"关键词匹配器初始化失败: {e}")


def _load_cookies_from_database(cookie_manager):
    """从数据库加载Cookie任务"""
    from app.repositories import db_manager
    
    cookies = db_manager.get_all_cookies_with_details()
    for cookie_id, details in cookies.items():
        cookie_value = details.get('value')
        user_id = details.get('user_id')
        if cookie_value:
            logger.info(f"启动数据库中的 Cookie 任务: {cookie_id} (用户ID: {user_id})")
            asyncio.run(cookie_manager.add_cookie_async(cookie_id, cookie_value, user_id=user_id, save_to_db=False))


def _create_cookie_manager():
    """创建并初始化CookieManager"""
    from app.repositories import db_manager
    logger.info("数据库管理器初始化完成")

    # 初始化规则引擎
    try:
        from app.core.rule_engine import rule_engine
        logger.info("规则引擎初始化完成")
    except ImportError as e:
        logger.warning(f"规则引擎导入失败: {e}")

    # 初始化关键词匹配器
    try:
        from app.core.keyword_matcher import keyword_matcher
        logger.info("关键词匹配器初始化完成")
    except ImportError as e:
        logger.warning(f"关键词匹配器导入失败: {e}")

    # 创建事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 创建CookieManager
    from app.core.cookie_manager import CookieManager
    cookie_manager = CookieManager(loop)
    logger.info("CookieManager 创建完成")

    # 从数据库加载Cookie任务
    logger.info("从数据库加载Cookie任务...")
    cookie_manager.reload_from_db()
    logger.info(f"已从数据库加载 {len(cookie_manager.cookies)} 个Cookie任务")

    # 从配置文件加载Cookie
    config_cookies = COOKIES_LIST
    for cookie in config_cookies:
        cookie_manager.add_cookie(cookie['id'], cookie['value'])
    logger.info(f"已从配置文件加载 {len(config_cookies)} 个Cookie")

    # 从环境变量加载Cookie
    env_cookie = os.getenv('XIAN_YU_COOKIE')
    if env_cookie:
        cookie_manager.add_cookie('env_cookie', env_cookie)
        logger.info("已从环境变量加载 1 个Cookie")
    else:
        logger.info("已从环境变量加载 0 个Cookie")

    return cookie_manager


def main():
    """主函数"""
    # 初始化数据库
    logger.info("开始启动主程序...")
    
    # 初始化文件日志收集器
    try:
        from scripts.file_log_collector import setup_file_logging
        setup_file_logging()
        logger.info("文件日志收集器已启动，开始收集实时日志")
    except ImportError as e:
        logger.warning(f"文件日志收集器导入失败：{e}")

    # 创建CookieManager
    cookie_manager = _create_cookie_manager()
    
    # 设置关键词匹配器回调
    _setup_keyword_matcher_callbacks(cookie_manager)

    # 启动API服务线程
    logger.info("启动 API 服务线程...")
    api_thread = threading.Thread(
        target=_start_api_server,
        daemon=True
    )
    api_thread.start()
    logger.info("API 服务线程已启动")
    
    logger.info("主程序启动完成，保持运行...")
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(3600)  # 每小时检查一次
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")


if __name__ == '__main__':
    main()
