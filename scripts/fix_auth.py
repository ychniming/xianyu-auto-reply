#!/usr/bin/env python3
"""
修复 reply_server/routes 中 auth 依赖问题的脚本

将 current_user: Dict[str, Any] = Depends(lambda: None)
替换为 current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
"""

import argparse
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

from loguru import logger


OLD_PATTERN = r"current_user:\s*Dict\[str,\s*Any\]\s*=\s*Depends\(\s*lambda:\s*None\s*\)"
NEW_PATTERN = "current_user: Optional[Dict[str, Any]] = Depends(get_current_user)"


def replace_in_file(filepath: str, backup: bool = True) -> Tuple[bool, bool]:
    """替换文件中的认证依赖模式

    Returns:
        (was_modified, had_error)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        new_content = re.sub(OLD_PATTERN, NEW_PATTERN, content)

        if new_content == original_content:
            return False, False

        if backup:
            backup_path = f"{filepath}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(filepath, backup_path)
            logger.info(f"已备份原文件: {backup_path}")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        logger.info(f"已修复: {filepath}")
        return True, False

    except Exception as e:
        logger.error(f"处理文件失败 {filepath}: {e}")
        return False, True


def find_routes_directory() -> Optional[str]:
    """查找 reply_server/routes 目录"""
    candidates = [
        Path("reply_server/routes"),
        Path(__file__).parent.parent / "reply_server/routes",
        Path("d:/我的/创业/xianyu-auto-reply-main/reply_server/routes"),
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return str(candidate)

    return None


def main():
    parser = argparse.ArgumentParser(description="修复 reply_server/routes 中的认证依赖问题")
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="reply_server/routes 目录路径"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="禁用自动备份"
    )
    args = parser.parse_args()

    routes_dir = args.path or find_routes_directory()

    if not routes_dir:
        logger.error("找不到 reply_server/routes 目录")
        return 1

    if not os.path.isdir(routes_dir):
        logger.error(f"路径不是有效目录: {routes_dir}")
        return 1

    backup = not args.no_backup
    total = 0
    modified = 0
    errors = 0

    for filename in os.listdir(routes_dir):
        if not filename.endswith('.py'):
            continue

        filepath = os.path.join(routes_dir, filename)
        total += 1

        was_modified, had_error = replace_in_file(filepath, backup=backup)
        if was_modified:
            modified += 1
        if had_error:
            errors += 1

    logger.info(f"处理完成: 共 {total} 个文件, 修改 {modified} 个, 错误 {errors} 个")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    exit(main())
