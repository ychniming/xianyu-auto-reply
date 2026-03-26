"""认证相关路由模块

提供登录、注册、验证码等认证相关接口
"""
from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
import secrets
from loguru import logger
from app.api.limiter import limiter
from app.api.response import success, error
from app.api.dependencies import get_token_data, verify_admin_token

router = APIRouter(prefix="", tags=["认证"])

security = HTTPBearer(auto_error=False)

# -------------------- 请求/响应模型 --------------------
class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    verification_code: Optional[str] = None


class LoginResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    verification_code: str


class RegisterResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class SendCodeResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class SendCodeRequest(BaseModel):
    email: str
    session_id: Optional[str] = None
    type: Optional[str] = 'register'


class CaptchaRequest(BaseModel):
    session_id: str


class CaptchaResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class VerifyCaptchaRequest(BaseModel):
    session_id: str
    captcha_code: str


class VerifyCaptchaResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


# -------------------- 辅助函数 --------------------
def generate_token() -> str:
    """生成随机token"""
    return secrets.token_urlsafe(32)


# -------------------- 路由 --------------------
@router.post('/login', response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest):
    """用户登录接口"""
    from app.repositories import db_manager

    ADMIN_USERNAME = "admin"
    TOKEN_EXPIRE_TIME = 24 * 60 * 60

    if req.username and req.password:
        logger.info(f"【{req.username}】尝试用户名登录")

        if db_manager.verify_user_password(req.username, req.password):
            user = db_manager.get_user_by_username(req.username)
            if user:
                token = generate_token()
                db_manager.create_session(token, user['id'], user['username'], TOKEN_EXPIRE_TIME)

                if user['username'] == ADMIN_USERNAME:
                    logger.info(f"【{user['username']}#{user['id']}】登录成功（管理员）")
                else:
                    logger.info(f"【{user['username']}#{user['id']}】登录成功")

                return LoginResponse(
                    code=200,
                    message="登录成功",
                    data={
                        "token": token,
                        "user_id": user['id'],
                        "username": user['username']
                    }
                )

        logger.warning(f"【{req.username}】登录失败：用户名或密码错误")
        return LoginResponse(
            code=401,
            message="用户名或密码错误"
        )

    elif req.email and req.password:
        logger.info(f"【{req.email}】尝试邮箱密码登录")

        user = db_manager.get_user_by_email(req.email)
        if user and db_manager.verify_user_password(user['username'], req.password):
            token = generate_token()
            db_manager.create_session(token, user['id'], user['username'], TOKEN_EXPIRE_TIME)

            logger.info(f"【{user['username']}#{user['id']}】邮箱登录成功")

            return LoginResponse(
                code=200,
                message="登录成功",
                data={
                    "token": token,
                    "user_id": user['id'],
                    "username": user['username']
                }
            )

        logger.warning(f"【{req.email}】邮箱登录失败：邮箱或密码错误")
        return LoginResponse(
            code=401,
            message="邮箱或密码错误"
        )

    elif req.email and req.verification_code:
        logger.info(f"【{req.email}】尝试邮箱验证码登录")

        if not db_manager.verify_email_code(req.email, req.verification_code, 'login'):
            logger.warning(f"【{req.email}】验证码登录失败：验证码错误或已过期")
            return LoginResponse(
                code=401,
                message="验证码错误或已过期"
            )

        user = db_manager.get_user_by_email(req.email)
        if not user:
            logger.warning(f"【{req.email}】验证码登录失败：用户不存在")
            return LoginResponse(
                code=404,
                message="用户不存在"
            )

        token = generate_token()
        db_manager.create_session(token, user['id'], user['username'], TOKEN_EXPIRE_TIME)

        logger.info(f"【{user['username']}#{user['id']}】验证码登录成功")

        return LoginResponse(
            code=200,
            message="登录成功",
            data={
                "token": token,
                "user_id": user['id'],
                "username": user['username']
            }
        )

    else:
        return LoginResponse(
            code=400,
            message="请提供有效的登录信息"
        )


@router.get('/verify')
@limiter.limit("60/minute")
async def verify(request: Request, user_info: Optional[Dict[str, Any]] = Depends(get_token_data)):
    """验证token接口"""
    if user_info:
        return success(data={
            "authenticated": True,
            "user_id": user_info['user_id'],
            "username": user_info['username']
        })
    return success(data={"authenticated": False})


@router.post('/logout')
async def logout(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """登出接口"""
    if credentials:
        from app.repositories import db_manager
        db_manager.delete_session(credentials.credentials)
    return success(message="已登出")


@router.post('/change-admin-password')
async def change_admin_password(request: ChangePasswordRequest, admin_user: Dict[str, Any] = Depends(verify_admin_token)):
    """修改管理员密码接口"""
    from app.repositories import db_manager

    try:
        if not db_manager.verify_user_password('admin', request.current_password):
            return error(code=400, message="当前密码错误")

        success_flag = db_manager.update_user_password('admin', request.new_password)

        if success_flag:
            logger.info(f"【admin#{admin_user['user_id']}】管理员密码修改成功")
            return success(message="密码修改成功")
        else:
            return error(code=500, message="密码修改失败")

    except Exception as e:
        logger.error(f"修改管理员密码异常: {e}")
        return error(code=500, message="系统错误")


@router.post('/generate-captcha', response_model=CaptchaResponse)
async def generate_captcha(request: CaptchaRequest):
    """生成图形验证码接口"""
    from app.repositories import db_manager

    try:
        captcha_text, captcha_image = db_manager.generate_captcha()

        if not captcha_image:
            return CaptchaResponse(
                code=500,
                message="图形验证码生成失败"
            )

        if db_manager.save_captcha(request.session_id, captcha_text):
            return CaptchaResponse(
                code=200,
                message="图形验证码生成成功",
                data={
                    "captcha_image": captcha_image,
                    "session_id": request.session_id
                }
            )
        else:
            return CaptchaResponse(
                code=500,
                message="图形验证码保存失败"
            )

    except Exception as e:
        logger.error(f"生成图形验证码失败: {e}")
        return CaptchaResponse(
            code=500,
            message="图形验证码生成失败"
        )


@router.post('/verify-captcha', response_model=VerifyCaptchaResponse)
async def verify_captcha(request: VerifyCaptchaRequest):
    """验证图形验证码接口"""
    from app.repositories import db_manager

    try:
        if db_manager.verify_captcha(request.session_id, request.captcha_code):
            return VerifyCaptchaResponse(
                code=200,
                message="图形验证码验证成功"
            )
        else:
            return VerifyCaptchaResponse(
                code=400,
                message="图形验证码错误或已过期"
            )

    except Exception as e:
        logger.error(f"验证图形验证码失败: {e}")
        return VerifyCaptchaResponse(
            code=500,
            message="图形验证码验证失败"
        )


@router.post('/send-verification-code', response_model=SendCodeResponse)
async def send_verification_code(request: SendCodeRequest):
    """发送验证码接口"""
    from app.repositories import db_manager

    try:
        if request.type == 'register':
            existing_user = db_manager.get_user_by_email(request.email)
            if existing_user:
                return SendCodeResponse(
                    code=400,
                    message="该邮箱已被注册"
                )
        elif request.type == 'login':
            existing_user = db_manager.get_user_by_email(request.email)
            if not existing_user:
                return SendCodeResponse(
                    code=404,
                    message="该邮箱未注册"
                )

        code = db_manager.generate_verification_code()

        if not db_manager.save_verification_code(request.email, code, request.type):
            return SendCodeResponse(
                code=500,
                message="验证码保存失败，请稍后重试"
            )

        if await db_manager.send_verification_email(request.email, code):
            return SendCodeResponse(
                code=200,
                message="验证码已发送到您的邮箱，请查收"
            )
        else:
            return SendCodeResponse(
                code=500,
                message="验证码发送失败，请检查邮箱地址或稍后重试"
            )

    except Exception as e:
        logger.error(f"发送验证码失败: {e}")
        return SendCodeResponse(
            code=500,
            message="发送验证码失败，请稍后重试"
        )


@router.post('/register', response_model=RegisterResponse)
@limiter.limit("3/minute")
async def register(request: Request, req: RegisterRequest):
    """用户注册接口"""
    from app.repositories import db_manager

    try:
        logger.info(f"【{req.username}】尝试注册，邮箱: {req.email}")

        if not db_manager.verify_email_code(req.email, req.verification_code):
            logger.warning(f"【{req.username}】注册失败: 验证码错误或已过期")
            return RegisterResponse(
                code=400,
                message="验证码错误或已过期"
            )

        existing_user = db_manager.get_user_by_username(req.username)
        if existing_user:
            logger.warning(f"【{req.username}】注册失败: 用户名已存在")
            return RegisterResponse(
                code=400,
                message="用户名已存在"
            )

        existing_email = db_manager.get_user_by_email(req.email)
        if existing_email:
            logger.warning(f"【{req.username}】注册失败: 邮箱已被注册")
            return RegisterResponse(
                code=400,
                message="该邮箱已被注册"
            )

        if db_manager.create_user(req.username, req.email, req.password):
            logger.info(f"【{req.username}】注册成功")
            return RegisterResponse(
                code=200,
                message="注册成功，请登录"
            )
        else:
            logger.error(f"【{req.username}】注册失败: 数据库操作失败")
            return RegisterResponse(
                code=500,
                message="注册失败，请稍后重试"
            )

    except Exception as e:
        logger.error(f"【{req.username}】注册异常: {e}")
        return RegisterResponse(
            code=500,
            message="注册失败，请稍后重试"
        )
