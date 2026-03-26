#!/usr/bin/env python3
"""API Key 加密迁移脚本

将数据库中明文存储的 API Key 迁移到加密字段

使用方法:
    python scripts/migrate_api_keys.py
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from loguru import logger
from app.repositories import db_manager
from app.utils.encryption import encrypt, EncryptionError


def migrate_api_keys() -> dict:
    """迁移所有明文 API Key 到加密字段
    
    Returns:
        dict: 迁移结果统计 {
            'total': 总记录数,
            'migrated': 成功迁移数,
            'skipped': 跳过数（已加密或为空）,
            'failed': 失败数
        }
    """
    stats = {
        'total': 0,
        'migrated': 0,
        'skipped': 0,
        'failed': 0
    }
    
    logger.info("开始迁移 API Key 到加密字段...")
    
    try:
        # 获取所有 AI 回复设置
        cursor = db_manager.conn.cursor()
        cursor.execute('''
            SELECT cookie_id, api_key, api_key_encrypted 
            FROM ai_reply_settings
        ''')
        
        rows = cursor.fetchall()
        stats['total'] = len(rows)
        
        for row in rows:
            cookie_id = row[0]
            api_key = row[1]
            api_key_encrypted = row[2]
            
            # 如果已经有加密字段，跳过
            if api_key_encrypted:
                logger.debug(f"账号 {cookie_id} 已有加密字段，跳过")
                stats['skipped'] += 1
                continue
            
            # 如果明文字段为空，跳过
            if not api_key:
                logger.debug(f"账号 {cookie_id} API Key 为空，跳过")
                stats['skipped'] += 1
                continue
            
            # 加密 API Key
            try:
                encrypted = encrypt(api_key)
                
                # 更新数据库
                cursor.execute('''
                    UPDATE ai_reply_settings 
                    SET api_key_encrypted = ?, api_key = ''
                    WHERE cookie_id = ?
                ''', (encrypted, cookie_id))
                
                logger.info(f"账号 {cookie_id} API Key 迁移成功")
                stats['migrated'] += 1
                
            except EncryptionError as e:
                logger.error(f"账号 {cookie_id} API Key 加密失败: {e}")
                stats['failed'] += 1
            except Exception as e:
                logger.error(f"账号 {cookie_id} 迁移失败: {e}")
                stats['failed'] += 1
        
        # 提交事务
        db_manager.conn.commit()
        
        logger.info("=" * 50)
        logger.info("API Key 迁移完成")
        logger.info(f"总记录数: {stats['total']}")
        logger.info(f"成功迁移: {stats['migrated']}")
        logger.info(f"跳过记录: {stats['skipped']}")
        logger.info(f"失败记录: {stats['failed']}")
        logger.info("=" * 50)
        
        return stats
        
    except Exception as e:
        logger.error(f"迁移过程失败: {e}")
        db_manager.conn.rollback()
        raise


def verify_migration() -> bool:
    """验证迁移结果
    
    Returns:
        bool: 验证是否通过
    """
    logger.info("开始验证迁移结果...")
    
    try:
        cursor = db_manager.conn.cursor()
        
        # 检查是否还有明文 API Key
        cursor.execute('''
            SELECT COUNT(*) FROM ai_reply_settings 
            WHERE api_key IS NOT NULL AND api_key != ''
        ''')
        plaintext_count = cursor.fetchone()[0]
        
        if plaintext_count > 0:
            logger.warning(f"发现 {plaintext_count} 条记录仍有明文 API Key")
            return False
        
        # 检查加密字段
        cursor.execute('''
            SELECT COUNT(*) FROM ai_reply_settings 
            WHERE api_key_encrypted IS NOT NULL AND api_key_encrypted != ''
        ''')
        encrypted_count = cursor.fetchone()[0]
        
        logger.info(f"验证通过: {encrypted_count} 条记录使用加密字段")
        return True
        
    except Exception as e:
        logger.error(f"验证失败: {e}")
        return False


def main():
    """主函数"""
    try:
        # 初始化数据库
        logger.info("初始化数据库连接...")
        
        # 执行迁移
        stats = migrate_api_keys()
        
        # 验证迁移
        if stats['migrated'] > 0:
            verify_migration()
        
        logger.info("迁移脚本执行完成")
        
        # 返回退出码
        if stats['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"迁移脚本执行失败: {e}")
        sys.exit(1)
    finally:
        # 关闭数据库连接
        db_manager.close()


if __name__ == "__main__":
    main()
