"""管理员路由模块

提供管理员专属的系统管理接口
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from loguru import logger

from app.api.dependencies import get_current_user

router = APIRouter(prefix="", tags=["管理员"])

# -------------------- 管理员认证 --------------------
def require_admin(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    """要求管理员权限"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未授权")
    if current_user['username'] != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


# -------------------- 用户管理 --------------------
@router.get('/admin/users')
def list_users(current_user: Dict[str, Any] = Depends(require_admin)):
    """获取所有用户列表"""
    try:
        from app.repositories import db_manager
        # 获取所有用户
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT id, username, email, is_active, created_at FROM users")
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'is_active': bool(row[3]),
                'created_at': row[4]
            })
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/admin/users/{user_id}')
def delete_user(user_id: int, current_user: Dict[str, Any] = Depends(require_admin)):
    """删除用户"""
    try:
        from app.repositories import db_manager
        cursor = db_manager.conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db_manager.conn.commit()
        return {'msg': 'deleted'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 日志管理 --------------------
@router.get("/logs")
def get_logs(
    current_user: Dict[str, Any] = Depends(require_admin),
    limit: int = 100,
    offset: int = 0
):
    """获取日志列表"""
    try:
        import os
        from pathlib import Path

        log_dir = Path(__file__).parent.parent.parent / "logs"
        if not log_dir.exists():
            return {"logs": [], "total": 0}

        log_files = list(log_dir.glob("xianyu_*.log"))
        logs = []

        for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 只返回最后limit行
                    start = max(0, len(lines) - limit)
                    end = len(lines)
                    file_logs = lines[start:end]

                    for i, line in enumerate(file_logs):
                        if offset > 0:
                            offset -= 1
                            continue
                        if len(logs) >= limit:
                            break
                        logs.append({
                            'file': log_file.name,
                            'line': start + i + 1,
                            'content': line.strip()
                        })
            except Exception as e:
                logger.error(f"读取日志文件失败: {log_file}, {e}")

        return {"logs": logs, "total": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stats")
def get_logs_stats(current_user: Dict[str, Any] = Depends(require_admin)):
    """获取日志统计"""
    try:
        import os
        from pathlib import Path
        from collections import Counter

        log_dir = Path(__file__).parent.parent.parent / "logs"
        if not log_dir.exists():
            return {"stats": {}}

        stats = Counter()
        log_files = list(log_dir.glob("xianyu_*.log"))

        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'ERROR' in line:
                            stats['error'] += 1
                        elif 'WARNING' in line:
                            stats['warning'] += 1
                        elif 'INFO' in line:
                            stats['info'] += 1
            except Exception as e:
                logger.warning(f"读取日志文件统计失败: {log_file}, {e}")

        return {"stats": dict(stats)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logs/clear")
def clear_logs(current_user: Dict[str, Any] = Depends(require_admin)):
    """清空日志文件"""
    try:
        import os
        from pathlib import Path

        log_dir = Path(__file__).parent.parent.parent / "logs"
        if not log_dir.exists():
            return {'msg': 'no logs to clear'}

        count = 0
        for log_file in log_dir.glob("xianyu_*.log"):
            try:
                with open(log_file, 'w') as f:
                    f.write('')
                count += 1
            except Exception as e:
                logger.warning(f"清空日志文件失败: {log_file}, {e}")

        return {'msg': f'cleared {count} log files'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 操作日志 --------------------
@router.get('/admin/logs')
def get_admin_logs(
    current_user: Dict[str, Any] = Depends(require_admin),
    limit: int = 100,
    offset: int = 0
):
    """获取管理员操作日志"""
    try:
        from app.repositories import db_manager
        cursor = db_manager.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM operation_logs")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT id, user_id, action, details, ip_address, created_at
            FROM operation_logs
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'user_id': row[1],
                'action': row[2],
                'details': row[3],
                'ip_address': row[4],
                'created_at': row[5]
            })

        return {"logs": logs, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 统计信息 --------------------
@router.get('/admin/stats')
def get_admin_stats(current_user: Dict[str, Any] = Depends(require_admin)):
    """获取系统统计信息"""
    try:
        from app.repositories import db_manager
        cursor = db_manager.conn.cursor()

        # 用户数
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        # Cookie数
        cursor.execute("SELECT COUNT(*) FROM cookies")
        cookie_count = cursor.fetchone()[0]

        # 关键字数
        cursor.execute("SELECT COUNT(*) FROM keywords")
        keyword_count = cursor.fetchone()[0]

        # 卡券数
        cursor.execute("SELECT COUNT(*) FROM cards")
        card_count = cursor.fetchone()[0]

        # 发货规则数
        cursor.execute("SELECT COUNT(*) FROM delivery_rules")
        rule_count = cursor.fetchone()[0]

        return {
            'user_count': user_count,
            'cookie_count': cookie_count,
            'keyword_count': keyword_count,
            'card_count': card_count,
            'rule_count': rule_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 备份管理 --------------------
@router.get("/admin/backup/download")
def download_backup(current_user: Dict[str, Any] = Depends(require_admin)):
    """下载备份"""
    try:
        from app.repositories import db_manager
        import json
        from fastapi.responses import StreamingResponse
        import io

        backup_data = db_manager.export_backup()
        json_str = json.dumps(backup_data, indent=2, ensure_ascii=False)

        output = io.BytesIO()
        output.write(json_str.encode('utf-8'))
        output.seek(0)

        return StreamingResponse(
            output,
            media_type='application/json',
            headers={'Content-Disposition': 'attachment;filename=backup.json'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/backup/upload")
async def upload_backup(file, current_user: Dict[str, Any] = Depends(require_admin)):
    """上传备份"""
    try:
        from app.repositories import db_manager
        import json

        contents = await file.read()
        backup_data = json.loads(contents)

        if db_manager.import_backup(backup_data):
            return {'msg': 'backup restored successfully'}
        else:
            raise HTTPException(status_code=500, detail="备份恢复失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/backup/list")
def list_backups(current_user: Dict[str, Any] = Depends(require_admin)):
    """列出可用备份"""
    try:
        from pathlib import Path
        import os

        backup_dir = Path(__file__).parent.parent.parent / "backups"
        if not backup_dir.exists():
            return {"backups": []}

        backups = []
        for f in sorted(backup_dir.glob("*.bak"), key=lambda x: x.stat().st_mtime, reverse=True):
            backups.append({
                'name': f.name,
                'size': f.stat().st_size,
                'modified': f.stat().st_mtime
            })

        return {"backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 数据库管理 --------------------
@router.get('/admin/data/{table_name}')
def get_table_data(table_name: str, current_user: Dict[str, Any] = Depends(require_admin)):
    """获取指定表的数据"""
    try:
        from app.repositories import db_manager
        cursor = db_manager.conn.cursor()

        # 安全检查：只允许查询已知表
        allowed_tables = [
            'users', 'cookies', 'keywords', 'cards', 'delivery_rules',
            'notification_channels', 'message_notifications', 'sessions',
            'system_settings', 'user_settings', 'ai_reply_settings',
            'item_info', 'default_replies', 'operation_logs'
        ]

        if table_name not in allowed_tables:
            raise HTTPException(status_code=403, detail="不允许查询该表")

        cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))

        return {"columns": columns, "data": data, "count": len(data)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
