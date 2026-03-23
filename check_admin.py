#!/usr/bin/env python3
"""
检查并重置管理员密码的脚本
"""
import hashlib
import sqlite3
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'xianyu_data.db')

def get_db_connection():
    """获取数据库连接"""
    if not os.path.exists(DB_PATH):
        # 尝试其他路径
        alt_paths = [
            'xianyu_data.db',
            os.path.join(os.path.dirname(__file__), 'xianyu_data.db'),
        ]
        for path in alt_paths:
            if os.path.exists(path):
                return sqlite3.connect(path)
        raise FileNotFoundError(f"找不到数据库文件: {DB_PATH}")
    return sqlite3.connect(DB_PATH)

def list_users():
    """列出所有用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, is_active, created_at FROM users')
    users = cursor.fetchall()
    conn.close()
    
    print("=" * 80)
    print("数据库中的用户列表:")
    print("=" * 80)
    print(f"{'ID':<5} {'用户名':<20} {'邮箱':<30} {'状态':<10} {'创建时间'}")
    print("-" * 80)
    for user in users:
        status = "激活" if user[3] else "禁用"
        print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {status:<10} {user[4]}")
    print("=" * 80)
    return users

def reset_admin_password(new_password="admin123"):
    """重置admin用户密码"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 计算密码哈希
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    # 检查admin用户是否存在
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    
    if result:
        # 更新密码
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = 'admin'",
            (password_hash,)
        )
        conn.commit()
        print(f"✅ admin 用户密码已重置为: {new_password}")
    else:
        # 创建admin用户
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            ('admin', 'admin@localhost', password_hash)
        )
        conn.commit()
        print(f"✅ admin 用户已创建，密码为: {new_password}")
    
    conn.close()

def verify_password(username, password):
    """验证用户密码"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        stored_hash = result[0]
        if stored_hash == password_hash:
            print(f"✅ 密码验证成功！用户名: {username}")
            return True
        else:
            print(f"❌ 密码验证失败！用户名: {username}")
            print(f"   存储的哈希: {stored_hash}")
            print(f"   输入的哈希: {password_hash}")
            return False
    else:
        print(f"❌ 用户不存在: {username}")
        return False

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 80)
    print("闲鱼自动回复系统 - 用户管理工具")
    print("=" * 80 + "\n")
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python check_admin.py list              - 列出所有用户")
        print("  python check_admin.py reset [密码]      - 重置admin密码")
        print("  python check_admin.py verify 用户名 密码 - 验证密码")
        print("\n")
        
        # 默认执行列出用户
        list_users()
    else:
        command = sys.argv[1]
        
        if command == "list":
            list_users()
        elif command == "reset":
            new_password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
            reset_admin_password(new_password)
        elif command == "verify":
            if len(sys.argv) < 4:
                print("用法: python check_admin.py verify <用户名> <密码>")
            else:
                verify_password(sys.argv[2], sys.argv[3])
        else:
            print(f"未知命令: {command}")
