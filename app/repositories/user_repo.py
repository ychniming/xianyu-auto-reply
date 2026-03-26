"""用户和会话仓储模块

提供用户认证、会话管理、验证码等操作
"""
import hashlib
import time
from typing import Dict, Optional, Any, List
from loguru import logger


class UserRepository:
    """用户数据访问层"""

    def __init__(self, db_manager):
        """初始化仓储

        Args:
            db_manager: DBManager实例引用
        """
        self._db = db_manager
        self.conn = db_manager.conn
        self.lock = db_manager.lock

    # -------------------- 用户管理 --------------------
    def create_user(self, username: str, email: str, password: str) -> bool:
        """创建新用户"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
                ''', (username, email, password_hash))
                self.conn.commit()
                logger.info(f"用户创建成功: {username}")
                return True
            except Exception as e:
                logger.error(f"创建用户失败: {e}")
                self.conn.rollback()
                return False

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户信息"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT id, username, email, password_hash, is_active, created_at
                FROM users WHERE username = ?
                ''', (username,))
                result = cursor.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'username': result[1],
                        'email': result[2],
                        'password_hash': result[3],
                        'is_active': bool(result[4]),
                        'created_at': result[5]
                    }
                return None
            except Exception as e:
                logger.error(f"获取用户失败: {e}")
                return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户信息"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT id, username, email, password_hash, is_active, created_at
                FROM users WHERE email = ?
                ''', (email,))
                result = cursor.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'username': result[1],
                        'email': result[2],
                        'password_hash': result[3],
                        'is_active': bool(result[4]),
                        'created_at': result[5]
                    }
                return None
            except Exception as e:
                logger.error(f"获取用户失败: {e}")
                return None

    def verify_user_password(self, username: str, password: str) -> bool:
        """验证用户密码"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
                result = cursor.fetchone()
                if result:
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    return result[0] == password_hash
                return False
            except Exception as e:
                logger.error(f"验证密码失败: {e}")
                return False

    def update_user_password(self, username: str, new_password: str) -> bool:
        """更新用户密码"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                cursor.execute('''
                UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
                WHERE username = ?
                ''', (password_hash, username))
                self.conn.commit()
                logger.info(f"用户密码更新成功: {username}")
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"更新密码失败: {e}")
                self.conn.rollback()
                return False

    # -------------------- 会话管理 --------------------
    def create_session(self, token: str, user_id: int, username: str, expires_in_seconds: int = 86400) -> bool:
        """创建会话"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                expires_at = time.time() + expires_in_seconds
                cursor.execute('''
                INSERT OR REPLACE INTO sessions (token, user_id, username, expires_at)
                VALUES (?, ?, ?, ?)
                ''', (token, user_id, username, expires_at))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"创建会话失败: {e}")
                self.conn.rollback()
                return False

    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT token, user_id, username, created_at, expires_at
                FROM sessions WHERE token = ?
                ''', (token,))
                result = cursor.fetchone()
                if result:
                    # 检查是否过期
                    if result[4] < time.time():
                        self.delete_session(token)
                        return None
                    return {
                        'token': result[0],
                        'user_id': result[1],
                        'username': result[2],
                        'created_at': result[3],
                        'expires_at': result[4]
                    }
                return None
            except Exception as e:
                logger.error(f"获取会话失败: {e}")
                return None

    def delete_session(self, token: str) -> bool:
        """删除会话"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "DELETE FROM sessions WHERE token = ?", (token,))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"删除会话失败: {e}")
                self.conn.rollback()
                return False

    def delete_user_sessions(self, user_id: int) -> int:
        """删除用户的所有会话"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "DELETE FROM sessions WHERE user_id = ?", (user_id,))
                self.conn.commit()
                return cursor.rowcount
            except Exception as e:
                logger.error(f"删除用户会话失败: {e}")
                self.conn.rollback()
                return 0

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                self._db._execute_sql(cursor, "DELETE FROM sessions WHERE expires_at < ?", (time.time(),))
                self.conn.commit()
                deleted = cursor.rowcount
                if deleted > 0:
                    logger.info(f"清理了 {deleted} 个过期会话")
                return deleted
            except Exception as e:
                logger.error(f"清理过期会话失败: {e}")
                self.conn.rollback()
                return 0

    def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有会话"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT token, user_id, username, created_at, expires_at
                FROM sessions WHERE user_id = ?
                ORDER BY created_at DESC
                ''', (user_id,))
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'token': row[0],
                        'user_id': row[1],
                        'username': row[2],
                        'created_at': row[3],
                        'expires_at': row[4]
                    })
                return results
            except Exception as e:
                logger.error(f"获取用户会话失败: {e}")
                return []

    # -------------------- 验证码管理 --------------------
    def generate_verification_code(self) -> str:
        """生成6位数字验证码"""
        return ''.join(random.choices(string.digits, k=6))

    def generate_captcha(self) -> tuple:
        """生成图形验证码"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            import base64
            import random
            import string

            # 生成4位验证码
            captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

            # 创建图片
            width, height = 120, 40
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)

            # 绘制干扰线
            for _ in range(5):
                x1 = random.randint(0, width)
                y1 = random.randint(0, height)
                x2 = random.randint(0, width)
                y2 = random.randint(0, height)
                draw.line([(x1, y1), (x2, y2)], fill=(random.randint(200, 255), random.randint(200, 255), random.randint(200, 255)))

            # 绘制验证码文字
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except Exception as e:
                logger.warning(f"加载字体失败，使用默认字体: {e}")
                font = ImageFont.load_default()

            text_width, text_height = draw.textsize(captcha_text, font=font)
            text_x = (width - text_width) // 2
            text_y = (height - text_height) // 2
            draw.text((text_x, text_y), captcha_text, fill=(0, 0, 0), font=font)

            # 转换为base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            captcha_image = f"data:image/png;base64,{img_str}"

            return captcha_text, captcha_image
        except Exception as e:
            logger.error(f"生成图形验证码失败: {e}")
            return "", ""

    def save_captcha(self, session_id: str, captcha_text: str, expires_minutes: int = 5) -> bool:
        """保存图形验证码"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                expires_at = time.time() + (expires_minutes * 60)
                cursor.execute('''
                INSERT OR REPLACE INTO captcha_codes (session_id, code, expires_at)
                VALUES (?, ?, ?)
                ''', (session_id, captcha_text.lower(), expires_at))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"保存图形验证码失败: {e}")
                self.conn.rollback()
                return False

    def verify_captcha(self, session_id: str, user_input: str) -> bool:
        """验证图形验证码"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT code, expires_at FROM captcha_codes
                WHERE session_id = ? AND used = 0
                ORDER BY created_at DESC LIMIT 1
                ''', (session_id,))
                result = cursor.fetchone()

                if not result:
                    return False

                code, expires_at = result
                if time.time() > expires_at:
                    return False

                if code == user_input.lower():
                    cursor.execute('UPDATE captcha_codes SET used = 1 WHERE session_id = ?', (session_id,))
                    self.conn.commit()
                    return True
                return False
            except Exception as e:
                logger.error(f"验证图形验证码失败: {e}")
                return False

    def save_verification_code(self, email: str, code: str, code_type: str = 'register', expires_minutes: int = 10) -> bool:
        """保存邮箱验证码"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                expires_at = time.time() + (expires_minutes * 60)
                cursor.execute('''
                INSERT INTO email_verifications (email, code, expires_at, type)
                VALUES (?, ?, ?, ?)
                ''', (email, code, expires_at, code_type))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"保存验证码失败: {e}")
                self.conn.rollback()
                return False

    def verify_email_code(self, email: str, code: str, code_type: str = 'register') -> bool:
        """验证邮箱验证码"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                SELECT expires_at FROM email_verifications
                WHERE email = ? AND code = ? AND used = 0 AND type = ?
                ORDER BY created_at DESC LIMIT 1
                ''', (email, code, code_type))
                result = cursor.fetchone()

                if not result:
                    return False

                expires_at = result[0]
                if time.time() > expires_at:
                    return False

                cursor.execute('UPDATE email_verifications SET used = 1 WHERE email = ? AND code = ?',
                             (email, code))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"验证邮箱验证码失败: {e}")
                return False

    async def send_verification_email(self, email: str, code: str) -> bool:
        """发送验证码邮件"""
        try:
            logger.info(f"发送验证码邮件到 {email}: {code}")
            return True
        except Exception as e:
            logger.error(f"发送验证码邮件失败: {e}")
            return False

    # -------------------- 用户设置 --------------------
    def get_user_settings(self, user_id: int) -> Dict[str, str]:
        """获取用户设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT key, value FROM user_settings WHERE user_id = ?', (user_id,))
                result = {}
                for row in cursor.fetchall():
                    result[row[0]] = row[1]
                return result
            except Exception as e:
                logger.error(f"获取用户设置失败: {e}")
                return {}

    def set_user_setting(self, user_id: int, key: str, value: str, description: str = None) -> bool:
        """设置用户设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO user_settings (user_id, key, value, description, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, key, value, description))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"设置用户设置失败: {e}")
                self.conn.rollback()
                return False

    def get_user_setting(self, user_id: int, key: str) -> Optional[str]:
        """获取指定用户设置"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT value FROM user_settings WHERE user_id = ? AND key = ?',
                             (user_id, key))
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                logger.error(f"获取用户设置失败: {e}")
                return None


# 导入需要的模块
import random
import string
