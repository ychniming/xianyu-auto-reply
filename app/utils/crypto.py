"""加密工具模块

提供Cookie加密存储功能，使用Fernet对称加密
"""
import os
import base64
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger


class CryptoError(Exception):
    """加密相关错误"""
    pass


class CookieEncryptor:
    """Cookie加密器
    
    使用Fernet对称加密算法对Cookie进行加密存储
    支持从环境变量或配置文件加载密钥
    """
    
    _instance = None
    _fernet: Optional[Fernet] = None
    _key_source: str = "unknown"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._fernet is not None:
            return
        
        key = self._load_key()
        if key:
            self._fernet = Fernet(key)
            logger.info(f"Cookie加密器初始化成功，密钥来源: {self._key_source}")
        else:
            logger.warning("未配置加密密钥，Cookie将以明文存储（不推荐）")
    
    def _load_key(self) -> Optional[bytes]:
        """加载加密密钥
        
        优先级：
        1. 环境变量 COOKIE_ENCRYPTION_KEY（必须是有效的Fernet密钥）
        2. 环境变量 COOKIE_ENCRYPTION_PASSWORD + COOKIE_ENCRYPTION_SALT（使用PBKDF2派生密钥）
        3. 返回None（不加密）
        
        Returns:
            Optional[bytes]: Fernet密钥或None
        """
        env_key = os.environ.get('COOKIE_ENCRYPTION_KEY')
        if env_key:
            try:
                key = env_key.encode() if len(env_key) == 44 else base64.urlsafe_b64decode(env_key)
                Fernet(key)
                self._key_source = "COOKIE_ENCRYPTION_KEY"
                return key
            except Exception as e:
                logger.warning(f"COOKIE_ENCRYPTION_KEY格式无效: {e}")
        
        env_password = os.environ.get('COOKIE_ENCRYPTION_PASSWORD')
        env_salt = os.environ.get('COOKIE_ENCRYPTION_SALT')
        
        if env_password:
            if not env_salt:
                logger.error("COOKIE_ENCRYPTION_PASSWORD已设置但COOKIE_ENCRYPTION_SALT未设置，请同时配置")
                return None
            key = self._derive_key_from_password(env_password, env_salt.encode())
            self._key_source = "COOKIE_ENCRYPTION_PASSWORD"
            return key
        
        return None
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """从密码派生Fernet密钥
        
        Args:
            password: 用户密码
            salt: 盐值
            
        Returns:
            bytes: Fernet密钥
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @property
    def is_enabled(self) -> bool:
        """检查加密是否启用"""
        return self._fernet is not None
    
    def encrypt(self, plaintext: str) -> str:
        """加密字符串
        
        Args:
            plaintext: 明文字符串
            
        Returns:
            str: 加密后的字符串（Base64编码）
            
        Raises:
            CryptoError: 加密失败
        """
        if not self._fernet:
            return plaintext
        
        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise CryptoError(f"加密失败: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """解密字符串
        
        Args:
            ciphertext: 加密字符串
            
        Returns:
            str: 解密后的明文
            
        Raises:
            CryptoError: 解密失败
        """
        if not self._fernet:
            return ciphertext
        
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.warning("解密失败：无效的令牌，可能数据未加密或密钥已更改")
            return ciphertext
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise CryptoError(f"解密失败: {e}")
    
    def is_encrypted(self, value: str) -> bool:
        """检查值是否已加密
        
        Args:
            value: 要检查的值
            
        Returns:
            bool: 是否已加密
        """
        if not self._fernet:
            return False
        
        try:
            self._fernet.decrypt(value.encode())
            return True
        except Exception:
            return False
    
    def decrypt_strict(self, ciphertext: str) -> str:
        """严格解密字符串（失败时抛出异常）
        
        Args:
            ciphertext: 加密字符串
            
        Returns:
            str: 解密后的明文
            
        Raises:
            CryptoError: 解密失败（包括数据未加密或密钥不匹配）
        """
        if not self._fernet:
            raise CryptoError("加密功能未启用")
        
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("解密失败：无效的令牌，数据可能被篡改或密钥已更改")
            raise CryptoError("解密失败：数据完整性验证失败")
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise CryptoError(f"解密失败: {e}")
    
    @staticmethod
    def generate_key() -> str:
        """生成新的Fernet密钥
        
        Returns:
            str: Base64编码的Fernet密钥
        """
        key = Fernet.generate_key()
        return key.decode()


cookie_encryptor = CookieEncryptor()
