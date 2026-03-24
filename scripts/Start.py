"""项目启动入口：

1. 创建 CookieManager，按配置文件 / 环境变量初始化账号任务
2. 在后台线程启动 FastAPI (reply_server) 提供管理与自动回复接口
3. 主协程保持运行
"""

import os
import sys
import asyncio
import threading
import uvicorn
from urllib.parse import urlparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from configs.config import AUTO_REPLY, COOKIES_LIST
from app.repositories import db_manager
from scripts.file_log_collector import setup_file_logging


def _start_api_server():
    """后台线程启动 FastAPI 服务"""
    api_conf = AUTO_REPLY.get('api', {})

    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '8082'))

    if 'host' in api_conf:
        host = api_conf['host']
    if 'port' in api_conf:
        port = api_conf['port']

    if 'url' in api_conf and 'host' not in api_conf and 'port' not in api_conf:
        url = api_conf.get('url', 'http://0.0.0.0:8082/xianyu/reply')
        parsed = urlparse(url)
        if parsed.hostname and parsed.hostname != 'localhost':
            host = parsed.hostname
        port = parsed.port or 8082

    logger.info(f"启动Web服务器: http://{host}:{port}")
    uvicorn.run("app.api:app", host=host, port=port, log_level="info")


def load_keywords_file(path: str):
    """从文件读取关键字 -> [(keyword, reply)]"""
    kw_list = []
    p = Path(path)
    if not p.exists():
        return kw_list
    with p.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '\t' in line:
                k, r = line.split('\t', 1)
            elif ' ' in line:
                k, r = line.split(' ', 1)
            elif ':' in line:
                k, r = line.split(':', 1)
            else:
                continue
            kw_list.append((k.strip(), r.strip()))
    return kw_list


def _setup_keyword_matcher_callbacks():
    """设置关键词匹配器回调函数，返回是否成功"""
    from app.repositories import db_manager
    from app.core.keyword_matcher import keyword_matcher

    try:
        from app.core.rule_engine import rule_engine
        logger.info("规则引擎初始化完成")
    except ImportError as e:
        logger.warning(f"规则引擎导入失败: {e}")

    keyword_matcher.set_sequence_index_updater(
        db_manager.keywords.update_sequence_index
    )
    keyword_matcher.set_trigger_count_updater(
        db_manager.increment_trigger_count
    )
    logger.info("关键词匹配器回调函数设置完成")
    return True


def _init_keyword_matcher():
    """初始化关键词匹配器"""
    try:
        from app.core.keyword_matcher import keyword_matcher
        _setup_keyword_matcher_callbacks()

        all_keywords = db_manager.get_all_keywords_with_type()

        if all_keywords:
            for cookie_id, keywords in all_keywords.items():
                if keywords:
                    keyword_matcher.build_automaton(cookie_id, keywords)
                    logger.info(f"初始化关键词匹配器: {cookie_id}, 关键词数量: {len(keywords)}")
            logger.info(f"关键词匹配器初始化完成，共 {len(all_keywords)} 个账号")
        else:
            logger.info("没有关键词数据，跳过关键词匹配器初始化")
        return True
    except Exception as e:
        logger.exception(f"初始化关键词匹配器失败: {e}")
        return False


def _load_cookies_from_database(manager):
    """从数据库加载的Cookie启动任务"""
    loaded = []
    for cid, val in manager.cookies.items():
        if not manager.get_cookie_status(cid):
            logger.info(f"跳过禁用的 Cookie: {cid}")
            continue

        try:
            cookie_info = db_manager.get_cookie_details(cid)
            user_id = cookie_info.get('user_id') if cookie_info else None
            loop = asyncio.get_running_loop()
            task = loop.create_task(manager._run_xianyu(cid, val, user_id))
            manager.tasks[cid] = task
            loaded.append(cid)
            logger.info(f"启动数据库中的 Cookie 任务: {cid} (用户ID: {user_id})")
        except Exception as e:
            logger.exception(f"启动 Cookie 任务失败: {cid}, {e}")
    return loaded


def _load_cookies_from_config(manager):
    """从配置文件加载新的Cookie"""
    loaded = []
    for entry in COOKIES_LIST:
        cid = entry.get('id')
        val = entry.get('value')
        if not cid or not val or cid in manager.cookies:
            continue

        kw_file = entry.get('keywords_file')
        kw_list = load_keywords_file(kw_file) if kw_file else None
        manager.add_cookie(cid, val, kw_list)
        loaded.append(cid)
        logger.info(f"从配置文件加载 Cookie: {cid}")
    return loaded


def _load_cookies_from_env(manager):
    """从环境变量加载单账号Cookie作为default"""
    env_cookie = os.getenv('COOKIES_STR')
    if env_cookie and 'default' not in manager.list_cookies():
        manager.add_cookie('default', env_cookie)
        logger.info("从环境变量加载 default Cookie")
        return ['default']
    return []


async def main():
    print("开始启动主程序...")

    print("初始化文件日志收集器...")
    setup_file_logging()
    logger.info("文件日志收集器已启动，开始收集实时日志")

    loop = asyncio.get_running_loop()

    print("创建 CookieManager...")
    from app.core import cookie_manager as cm
    from app.core.cookie_manager import CookieManager
    cm.manager = CookieManager(loop)
    manager = cm.manager
    print("CookieManager 创建完成")

    print("初始化关键词匹配器...")
    _init_keyword_matcher()

    print("从数据库加载Cookie任务...")
    db_loaded = _load_cookies_from_database(manager)
    logger.info(f"已从数据库加载 {len(db_loaded)} 个Cookie任务，当前任务数: {len(manager.tasks)}")

    config_loaded = _load_cookies_from_config(manager)
    logger.info(f"已从配置文件加载 {len(config_loaded)} 个Cookie")

    env_loaded = _load_cookies_from_env(manager)
    logger.info(f"已从环境变量加载 {len(env_loaded)} 个Cookie")

    print("启动 API 服务线程...")
    threading.Thread(target=_start_api_server, daemon=True).start()
    print("API 服务线程已启动")

    print("主程序启动完成，保持运行...")
    await asyncio.Event().wait()


if __name__ == '__main__':
    asyncio.run(main())
