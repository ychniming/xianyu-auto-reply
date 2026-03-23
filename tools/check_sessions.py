"""
检查数据库中的会话状态
"""

import sqlite3
from pathlib import Path

db_path = Path("xianyu_data.db")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 检查 sessions 表
cursor.execute("SELECT COUNT(*) FROM sessions")
count = cursor.fetchone()[0]
print(f"会话总数：{count}")

# 检查未过期的会话
cursor.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > strftime('%s', 'now')")
valid_count = cursor.fetchone()[0]
print(f"有效会话数：{valid_count}")

# 显示所有会话
cursor.execute("PRAGMA table_info(sessions)")
columns = cursor.fetchall()
print(f"\nsessions 表结构：{[col[1] for col in columns]}")

cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT 10")
sessions = cursor.fetchall()

print("\n最近 10 个会话:")
for session in sessions:
    print(f"  {session}")

conn.close()
