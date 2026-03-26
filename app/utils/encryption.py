"""加密工具模块

提供 AES-256-GCM 加密和解密功能，用于保护敏感数据（如 Cookie、Token 等）
"""

import base64
import os
import secrets
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger

# 环境变量名称
ENCRYPTION_KEY_ENV = "ENCRYPTION_KEY"
# 密钥长度（32 字节 = 256 位）
KEY_LENGTH = 32
# 盐值长度
SALT_LENGTH = 16
# 随机数长度（12 字节，符合 GCM 标准）
NONCE_LENGTH = 12


class EncryptionError(Exception):
    """加密/解密过程中的错误异常"""

    pass


def _get_project_root() -> Path:
    """获取项目根目录路径

    Returns:
        Path: 项目根目录路径
    """
    current_file = Path(__file__).resolve()
    # app/utils -> app -> 项目根目录
    return current_file.parent.parent.parent


def _get_env_file_path() -> Path:
    """获取 .env 文件路径

    Returns:
        Path: .env 文件路径
    """
    return _get_project_root() / ".env"


def _read_env_file() -> dict:
    """读取 .env 文件内容

    Returns:
        dict: 环境变量字典
    """
    env_path = _get_env_file_path()
    env_vars = {}

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue
                # 解析 KEY=VALUE 格式
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

    return env_vars


def _write_env_file(env_vars: dict) -> None:
    """写入环境变量到 .env 文件

    Args:
        env_vars: 环境变量字典
    """
    env_path = _get_env_file_path()
    lines = []

    # 读取现有内容
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                # 保留非加密相关的行
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    key = stripped.split("=", 1)[0].strip() if "=" in stripped else ""
                    if key and key != ENCRYPTION_KEY_ENV:
                        lines.append(line.rstrip())
                else:
                    lines.append(line.rstrip())

    # 添加加密密钥（如果不存在）
    if ENCRYPTION_KEY_ENV not in env_vars:
        # 查找插入位置（在现有内容之后）
        if lines and lines[-1].strip():
            lines.append("")

    # 更新或添加加密密钥
    key_found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{ENCRYPTION_KEY_ENV}="):
            lines[i] = f"{ENCRYPTION_KEY_ENV}={env_vars[ENCRYPTION_KEY_ENV]}"
            key_found = True
            break

    if not key_found:
        lines.append(f"{ENCRYPTION_KEY_ENV}={env_vars[ENCRYPTION_KEY_ENV]}")

    # 写入文件
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _generate_encryption_key() -> str:
    """生成新的加密密钥（Base64 编码）

    Returns:
        str: Base64 编码的密钥
    """
    # 生成 32 字节随机密钥
    key_bytes = secrets.token_bytes(KEY_LENGTH)
    # 返回 Base64 编码字符串
    return base64.b64encode(key_bytes).decode("utf-8")


def _derive_key_from_password(password: str, salt: bytes) -> bytes:
    """从密码派生密钥（用于密码学目的）

    Args:
        password: 密码
        salt: 盐值

    Returns:
        bytes: 派生的密钥（32 字节）
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(password.encode("utf-8"))


def get_encryption_key() -> bytes:
    """获取加密密钥

    从环境变量 ENCRYPTION_KEY 读取密钥，如果不存在则生成并保存到 .env 文件

    Returns:
        bytes: 32 字节（256 位）加密密钥

    Raises:
        EncryptionError: 当密钥无效或读取失败时
    """
    # 优先从环境变量读取
    key_str = os.environ.get(ENCRYPTION_KEY_ENV)

    if not key_str:
        # 从 .env 文件读取
        env_vars = _read_env_file()
        key_str = env_vars.get(ENCRYPTION_KEY_ENV)

    if not key_str:
        # 生成新密钥
        key_str = _generate_encryption_key()
        # 保存到 .env 文件
        env_vars = {ENCRYPTION_KEY_ENV: key_str}
        _write_env_file(env_vars)
        logger.info(f"已生成新的加密密钥并保存到 .env 文件")

        # 设置环境变量供当前进程使用
        os.environ[ENCRYPTION_KEY_ENV] = key_str

    try:
        # 解码 Base64 密钥
        key_bytes = base64.b64decode(key_str)

        # 验证密钥长度
        if len(key_bytes) != KEY_LENGTH:
            raise EncryptionError(
                f"密钥长度无效: 期望 {KEY_LENGTH} 字节，实际 {len(key_bytes)} 字节"
            )

        return key_bytes

    except ValueError as e:
        logger.error(f"密钥 Base64 解码失败: {e}")
        raise EncryptionError(f"密钥格式无效: {e}")
    except Exception as e:
        logger.error(f"获取加密密钥失败: {e}")
        raise EncryptionError(f"获取加密密钥失败: {e}")


def encrypt(data: str) -> str:
    """加密字符串数据

    使用 AES-256-GCM 算法加密数据，返回 Base64 编码的密文
    密文格式：盐值(16字节) + 随机数(12字节) + 密文

    Args:
        data: 要加密的明文字符串

    Returns:
        str: Base64 编码的密文

    Raises:
        EncryptionError: 加密失败时抛出
    """
    if not data:
        raise EncryptionError("加密数据不能为空")

    try:
        # 获取加密密钥
        key = get_encryption_key()

        # 生成随机盐值和随机数
        salt = secrets.token_bytes(SALT_LENGTH)
        nonce = secrets.token_bytes(NONCE_LENGTH)

        # 将盐值混入密钥（增加安全性）
        derived_key = _derive_key_from_password(
            base64.b64encode(key).decode("utf-8"), salt
        )

        # 使用派生密钥创建 AESGCM 实例
        aesgcm = AESGCM(derived_key)

        # 加密数据
        ciphertext = aesgcm.encrypt(nonce, data.encode("utf-8"), None)

        # 拼接：盐值 + 随机数 + 密文
        encrypted_data = salt + nonce + ciphertext

        # 返回 Base64 编码
        return base64.b64encode(encrypted_data).decode("utf-8")

    except EncryptionError:
        # 重新抛出加密错误
        raise
    except Exception as e:
        logger.error(f"加密数据失败: {e}")
        raise EncryptionError(f"加密失败: {e}")


def decrypt(encrypted_data: str) -> str:
    """解密字符串数据

    解密使用 AES-256-GCM 加密的 Base64 编码密文

    Args:
        encrypted_data: Base64 编码的密文

    Returns:
        str: 解密后的明文字符串

    Raises:
        EncryptionError: 解密失败时抛出
    """
    if not encrypted_data:
        raise EncryptionError("解密数据不能为空")

    try:
        # 获取加密密钥
        key = get_encryption_key()

        # 解码 Base64
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
        except ValueError as e:
            raise EncryptionError(f"密文 Base64 解码失败: {e}")

        # 验证数据长度
        min_length = SALT_LENGTH + NONCE_LENGTH + 1
        if len(encrypted_bytes) < min_length:
            raise EncryptionError(
                f"密文长度不足: 最小 {min_length} 字节，实际 {len(encrypted_bytes)} 字节"
            )

        # 提取盐值、随机数和密文
        salt = encrypted_bytes[:SALT_LENGTH]
        nonce = encrypted_bytes[SALT_LENGTH : SALT_LENGTH + NONCE_LENGTH]
        ciphertext = encrypted_bytes[SALT_LENGTH + NONCE_LENGTH :]

        # 派生密钥
        derived_key = _derive_key_from_password(
            base64.b64encode(key).decode("utf-8"), salt
        )

        # 解密数据
        aesgcm = AESGCM(derived_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext.decode("utf-8")

    except EncryptionError:
        # 重新抛出加密错误
        raise
    except Exception as e:
        logger.error(f"解密数据失败: {e}")
        raise EncryptionError(f"解密失败: {e}")


# 模块级别的密钥缓存（避免频繁读取文件）
_cached_key: Optional[bytes] = None


def get_encryption_key_cached() -> bytes:
    """获取加密密钥（带缓存）

    缓存密钥以提高性能，适用于需要频繁加密/解密的场景

    Returns:
        bytes: 32 字节（256 位）加密密钥
    """
    global _cached_key

    if _cached_key is None:
        _cached_key = get_encryption_key()

    return _cached_key


def clear_key_cache() -> None:
    """清除密钥缓存

    在密钥更新后调用此函数以清除缓存
    """
    global _cached_key
    _cached_key = None
    logger.info("加密密钥缓存已清除")


__all__ = [
    "EncryptionError",
    "encrypt",
    "decrypt",
    "get_encryption_key",
    "get_encryption_key_cached",
    "clear_key_cache",
]
