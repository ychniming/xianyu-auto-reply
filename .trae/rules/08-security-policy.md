# 安全策略

[返回主目录](./project_rules.md)

---

## 8.1 认证与授权

### JWT 认证

```python
# Token 生成
from datetime import datetime, timedelta
import jwt

def create_access_token(user_id: int, username: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Token 验证
def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "无效Token")
```

### 权限控制

```python
from functools import wraps

def require_admin(func):
    """管理员权限装饰器"""
    @wraps(func)
    async def wrapper(*args, current_user, **kwargs):
        if current_user.role != "admin":
            raise HTTPException(403, "需要管理员权限")
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper

def require_owner(func):
    """资源所有者权限装饰器"""
    @wraps(func)
    async def wrapper(*args, current_user, resource_id, **kwargs):
        if not is_owner(current_user, resource_id):
            raise HTTPException(403, "无权访问此资源")
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper
```

---

## 8.2 数据安全

### 敏感数据处理

```python
# 密码加密
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Cookie 加密存储
from cryptography.fernet import Fernet

def encrypt_cookie(cookie: str) -> str:
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(cookie.encode()).decode()

def decrypt_cookie(encrypted: str) -> str:
    f = Fernet(ENCRYPTION_KEY)
    return f.decrypt(encrypted.encode()).decode()
```

### SQL 注入防护

```python
# 使用参数化查询
def get_user_by_username(username: str) -> dict:
    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)  # 参数化
    )
    return cursor.fetchone()

# 错误示例（不要这样写）
# cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

---

## 8.3 API 安全

### 请求限流

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/login")
@limiter.limit("5/minute")  # 每分钟最多5次
async def login(request: Request, credentials: LoginRequest):
    pass
```

### 输入验证

```python
from pydantic import BaseModel, validator, constr

class CookieCreate(BaseModel):
    cookie_id: constr(min_length=1, max_length=50)
    cookie_value: constr(min_length=10, max_length=10000)
    
    @validator('cookie_id')
    def validate_cookie_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('cookie_id只能包含字母、数字、下划线和连字符')
        return v
```

---

## 8.4 安全检查清单

### 代码层面

- [ ] 所有用户输入都经过验证
- [ ] 敏感数据加密存储
- [ ] 使用参数化SQL查询
- [ ] 实现请求限流
- [ ] 错误信息不暴露敏感信息

### 配置层面

- [ ] JWT密钥足够复杂
- [ ] 默认密码已修改
- [ ] HTTPS已启用
- [ ] 敏感文件不提交Git
- [ ] 日志不记录敏感信息

### 运维层面

- [ ] 防火墙已配置
- [ ] 定期安全扫描
- [ ] 定期更新依赖
- [ ] 监控异常登录
- [ ] 定期备份数据
