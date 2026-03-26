#!/usr/bin/env python3
"""Cookie加密迁移脚本

将数据库中的明文Cookie迁移到加密存储

使用方法:
    python scripts/migrate_cookies.py [--dry-run]

参数:
    --dry-run: 仅模拟运行，不实际修改数据库

注意:
    - 运行前请确保已备份数据库
    - 运行前请确保已配置加密密钥（ENCRYPTION_KEY环境变量）
    - 运行后明文Cookie字段将被清空
"""

import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from app.repositories.base import BaseDB
from app.utils.encryption import encrypt, EncryptionError


def migrate_cookies(db_path: str, dry_run: bool = False) -> dict:
    """迁移Cookie数据到加密存储
    
    Args:
        db_path: 数据库文件路径
        dry_run: 是否仅模拟运行
        
    Returns:
        dict: 迁移统计信息
    """
    stats = {
        'total': 0,
        'migrated': 0,
        'skipped': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        # 初始化数据库连接
        db = BaseDB(db_path)
        db.init_db()
        
        # 获取所有Cookie
        cursor = db.conn.cursor()
        cursor.execute("SELECT id, value, value_encrypted FROM cookies")
        cookies = cursor.fetchall()
        
        stats['total'] = len(cookies)
        logger.info(f"找到 {stats['total']} 个Cookie记录")
        
        if stats['total'] == 0:
            logger.info("没有需要迁移的Cookie数据")
            return stats
        
        # 遍历并迁移每个Cookie
        for cookie_id, plain_value, encrypted_value in cookies:
            try:
                # 如果已经加密，跳过
                if encrypted_value:
                    logger.info(f"Cookie {cookie_id} 已加密，跳过")
                    stats['skipped'] += 1
                    continue
                
                # 如果没有明文值，跳过
                if not plain_value:
                    logger.warning(f"Cookie {cookie_id} 没有明文值，跳过")
                    stats['skipped'] += 1
                    continue
                
                # 加密Cookie值
                logger.info(f"正在迁移Cookie: {cookie_id}")
                encrypted = encrypt(plain_value)
                
                if not dry_run:
                    # 更新数据库
                    cursor.execute(
                        "UPDATE cookies SET value_encrypted = ?, value = NULL WHERE id = ?",
                        (encrypted, cookie_id)
                    )
                    logger.info(f"Cookie {cookie_id} 迁移成功")
                else:
                    logger.info(f"[模拟] Cookie {cookie_id} 将被迁移")
                
                stats['migrated'] += 1
                
            except EncryptionError as e:
                error_msg = f"Cookie {cookie_id} 加密失败: {e}"
                logger.error(error_msg)
                stats['failed'] += 1
                stats['errors'].append(error_msg)
            except Exception as e:
                error_msg = f"Cookie {cookie_id} 迁移失败: {e}"
                logger.error(error_msg)
                stats['failed'] += 1
                stats['errors'].append(error_msg)
        
        # 提交事务
        if not dry_run and stats['migrated'] > 0:
            db.conn.commit()
            logger.info(f"成功提交 {stats['migrated']} 个Cookie的迁移")
        
        # 关闭数据库连接
        db.close()
        
    except Exception as e:
        logger.error(f"迁移过程失败: {e}")
        stats['errors'].append(f"迁移过程失败: {e}")
    
    return stats


def print_summary(stats: dict, dry_run: bool = False) -> None:
    """打印迁移摘要
    
    Args:
        stats: 迁移统计信息
        dry_run: 是否为模拟运行
    """
    print("\n" + "=" * 60)
    print("Cookie加密迁移摘要")
    print("=" * 60)
    
    if dry_run:
        print("【模拟运行模式】")
    
    print(f"总记录数: {stats['total']}")
    print(f"已迁移: {stats['migrated']}")
    print(f"已跳过: {stats['skipped']}")
    print(f"失败: {stats['failed']}")
    
    if stats['errors']:
        print("\n错误详情:")
        for i, error in enumerate(stats['errors'], 1):
            print(f"  {i}. {error}")
    
    print("=" * 60)
    
    if stats['failed'] > 0:
        print("⚠️  迁移过程中出现错误，请检查日志")
        sys.exit(1)
    elif stats['migrated'] > 0:
        if dry_run:
            print("✅ 模拟运行完成，请移除 --dry-run 参数执行实际迁移")
        else:
            print("✅ 迁移完成！所有Cookie已加密存储")
    else:
        print("ℹ️  没有需要迁移的Cookie数据")


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='Cookie加密迁移脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 模拟运行
  python scripts/migrate_cookies.py --dry-run
  
  # 实际迁移
  python scripts/migrate_cookies.py
  
注意:
  - 运行前请确保已备份数据库
  - 运行前请确保已配置加密密钥（ENCRYPTION_KEY环境变量）
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅模拟运行，不实际修改数据库'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='数据库文件路径（默认使用环境变量DB_PATH或xianyu_data.db）'
    )
    
    args = parser.parse_args()
    
    # 确定数据库路径
    db_path = args.db_path or os.getenv('DB_PATH', 'xianyu_data.db')
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        sys.exit(1)
    
    logger.info(f"数据库路径: {db_path}")
    
    if args.dry_run:
        logger.info("【模拟运行模式】不会实际修改数据库")
    else:
        # 提示用户确认
        print("\n⚠️  警告: 此操作将修改数据库中的Cookie数据")
        print(f"数据库路径: {db_path}")
        print("建议在运行前备份数据库文件")
        
        response = input("\n是否继续? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("已取消操作")
            sys.exit(0)
    
    # 执行迁移
    stats = migrate_cookies(db_path, args.dry_run)
    
    # 打印摘要
    print_summary(stats, args.dry_run)


if __name__ == '__main__':
    main()
