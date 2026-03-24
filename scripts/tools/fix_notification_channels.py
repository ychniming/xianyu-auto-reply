"""
修复 notification_channels 表的 user_id 约束
"""

import sqlite3
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / "xianyu_data.db"

print(f"数据库路径：{db_path}")
print(f"数据库存在：{db_path.exists()}")

conn = None

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute("PRAGMA table_info(notification_channels)")
    columns = cursor.fetchall()
    
    print("\n当前表结构:")
    for col in columns:
        print(f"  {col[1]}: {col[2]} (NOT NULL: {col[3]})")
    
    # 修改 user_id 列，允许 NULL
    print("\n修改 user_id 列为允许 NULL...")
    
    # SQLite 不支持直接修改列约束，需要重建表
    cursor.execute("PRAGMA foreign_keys=0")
    
    # 创建临时表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notification_channels_temp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        config TEXT NOT NULL,
        user_id INTEGER,
        enabled INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # 复制数据
    cursor.execute('''
    INSERT INTO notification_channels_temp (id, name, type, config, user_id, enabled, created_at, updated_at)
    SELECT id, name, type, config, user_id, enabled, created_at, updated_at
    FROM notification_channels
    ''')
    
    # 删除旧表
    cursor.execute('DROP TABLE notification_channels')
    
    # 重命名临时表
    cursor.execute('ALTER TABLE notification_channels_temp RENAME TO notification_channels')
    
    # 重建索引和触发器
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_notification_channels_updated_at
    AFTER UPDATE ON notification_channels
    BEGIN
        UPDATE notification_channels SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END
    ''')
    
    cursor.execute('PRAGMA foreign_keys=1')
    
    conn.commit()
    
    # 验证修改
    cursor.execute("PRAGMA table_info(notification_channels)")
    columns = cursor.fetchall()
    
    print("\n修改后的表结构:")
    for col in columns:
        print(f"  {col[1]}: {col[2]} (NOT NULL: {col[3]})")
    
    print("\n✅ 数据库表修复成功！")
    
except Exception as e:
    print(f"❌ 修复失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if conn:
        conn.close()
