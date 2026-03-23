"""
发货模块公共基类
提供自动发货功能的公共基础功能
"""
import time
import asyncio
import json
from typing import Optional, Dict, Any, Callable, Type, Union
from abc import ABC
from functools import wraps
from utils.xianyu_utils import trans_cookies, generate_sign
from loguru import logger


class RetryableError(Exception):
    """可重试的错误基类"""
    pass


# 模块级常量
API_VERSION = '2.7.2'
APP_KEY = '34839810'
BASE_API_URL = 'https://h5api.m.goofish.com/h5/'


class TokenExpiredError(RetryableError):
    """Token过期错误"""
    pass


class NetworkError(RetryableError):
    """网络错误"""
    pass


class RetryConfig:
    """重试配置类

    定义统一的重试策略配置。

    Attributes:
        max_retries: 最大重试次数，默认3次
        base_delay: 基础延迟时间（秒），默认0.5秒
        backoff_multiplier: 退避乘数，默认2.0
        retryable_exceptions: 需要重试的异常类型列表
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.5,
        backoff_multiplier: float = 2.0,
        retryable_exceptions: Optional[tuple] = None
    ):
        """初始化重试配置

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            backoff_multiplier: 退避乘数
            retryable_exceptions: 需要重试的异常类型元组
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_multiplier = backoff_multiplier
        self.retryable_exceptions = retryable_exceptions or (
            TokenExpiredError,
            NetworkError,
            asyncio.TimeoutError,
            ConnectionError,
        )

    def get_delay(self, attempt: int) -> float:
        """获取第N次重试的延迟时间

        使用指数退避算法计算延迟时间。

        Args:
            attempt: 当前重试次数（从1开始）

        Returns:
            float: 延迟时间（秒）
        """
        return self.base_delay * (self.backoff_multiplier ** (attempt - 1))


# 默认重试配置
DEFAULT_RETRY_CONFIG = RetryConfig()


def retry_with_config(
    config: RetryConfig = DEFAULT_RETRY_CONFIG,
    operation_name: str = "操作"
):
    """重试装饰器

    为异步函数提供统一的重试机制，支持指数退避。

    Args:
        config: 重试配置，默认使用 DEFAULT_RETRY_CONFIG
        operation_name: 操作名称，用于日志记录

    Returns:
        Callable: 装饰器函数

    Example:
        @retry_with_config(operation_name="发货")
        async def ship_order(self, order_id: str) -> Dict[str, Any]:
            # 发货逻辑
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # 检查是否是可重试的异常
                    if not isinstance(e, config.retryable_exceptions):
                        logger.error(f"【{operation_name}】发生不可重试的错误: {e}")
                        raise

                    # 如果已达到最大重试次数，抛出最后一次异常
                    if attempt >= config.max_retries:
                        logger.error(
                            f"【{operation_name}】重试{config.max_retries}次后仍然失败，"
                            f"最后错误: {e}"
                        )
                        raise last_exception

                    # 计算延迟时间
                    delay = config.get_delay(attempt + 1)
                    logger.warning(
                        f"【{operation_name}】第{attempt + 1}次尝试失败: {e}，"
                        f"{delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)

            # 理论上不会执行到这里
            raise last_exception if last_exception else Exception("未知错误")

        return wrapper
    return decorator


class RetryExecutor:
    """重试执行器

    提供统一的重试执行机制，适用于需要在重试前执行特定操作（如刷新Token）的场景。

    Attributes:
        config: 重试配置
        operation_name: 操作名称
        on_retry: 重试回调函数
    """

    def __init__(
        self,
        config: RetryConfig = DEFAULT_RETRY_CONFIG,
        operation_name: str = "操作",
        on_retry: Optional[Callable[[int], None]] = None
    ):
        """初始化重试执行器

        Args:
            config: 重试配置
            operation_name: 操作名称
            on_retry: 重试回调函数，接收当前重试次数作为参数
        """
        self.config = config
        self.operation_name = operation_name
        self.on_retry = on_retry
        self._attempt = 0
        self._last_exception = None

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """执行带重试的函数

        Args:
            func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Any: 函数执行结果

        Raises:
            Exception: 当重试次数用尽后仍失败时抛出最后一次异常
        """
        for attempt in range(self.config.max_retries + 1):
            self._attempt = attempt
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self._last_exception = e

                # 检查是否是可重试的异常
                if not isinstance(e, self.config.retryable_exceptions):
                    logger.error(f"【{self.operation_name}】发生不可重试的错误: {e}")
                    raise

                # 如果已达到最大重试次数，抛出最后一次异常
                if attempt >= self.config.max_retries:
                    logger.error(
                        f"【{self.operation_name}】重试{self.config.max_retries}次后仍然失败，"
                        f"最后错误: {e}"
                    )
                    raise self._last_exception

                # 计算延迟时间
                delay = self.config.get_delay(attempt + 1)
                logger.warning(
                    f"【{self.operation_name}】第{attempt + 1}次尝试失败: {e}，"
                    f"{delay}秒后重试..."
                )

                # 执行重试回调
                if self.on_retry:
                    await self.on_retry(attempt + 1)

                await asyncio.sleep(delay)

        # 理论上不会执行到这里
        raise self._last_exception if self._last_exception else Exception("未知错误")

    @property
    def attempt(self) -> int:
        """获取当前尝试次数"""
        return self._attempt


# 为了向后兼容，保留 RetryContext 作为 RetryExecutor 的别名
RetryContext = RetryExecutor


class BaseDelivery(ABC):
    """自动发货处理器基类

    提供发货功能的基础功能，包括：
    - Cookie 解析和管理
    - 安全字符串转换
    - Cookie 更新和持久化
    - 敏感信息脱敏
    - 统一的重试机制

    Attributes:
        session: HTTP 会话对象
        cookies_str: Cookie 字符串
        cookie_id: Cookie 标识
        cookies: 解析后的 Cookie 字典
        current_token: 当前 token
        last_token_refresh_time: 上次 token 刷新时间
        token_refresh_interval: token 刷新间隔（秒）
        refresh_token: token 刷新回调函数
        retry_config: 重试配置
    """

    def __init__(
        self,
        session: Any,
        cookies_str: str,
        cookie_id: str,
        retry_config: Optional[RetryConfig] = None
    ):
        """初始化发货处理器

        Args:
            session: HTTP 会话对象
            cookies_str: Cookie 字符串
            cookie_id: Cookie 标识
            retry_config: 重试配置，默认使用 DEFAULT_RETRY_CONFIG
        """
        self.session = session
        self.cookies_str = cookies_str
        self.cookie_id = cookie_id
        self.cookies: Dict[str, str] = {}
        self.current_token: Optional[str] = None
        self.last_token_refresh_time: float = 0
        self.token_refresh_interval: int = 3600
        self.refresh_token: Optional[callable] = None
        self.retry_config = retry_config or DEFAULT_RETRY_CONFIG

        # 解析 cookies
        self._parse_cookies(cookies_str)

    def _parse_cookies(self, cookies_str: str) -> None:
        """解析 cookie 字符串

        Args:
            cookies_str: Cookie 字符串，格式为 "key1=value1; key2=value2"
        """
        if not cookies_str:
            return

        for cookie in cookies_str.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                self.cookies[key.strip()] = value.strip()

    def _safe_str(self, obj: Any) -> str:
        """安全字符串转换

        将对象安全地转换为字符串，捕获所有异常。

        Args:
            obj: 任意对象

        Returns:
            str: 对象的字符串表示，转换失败时返回默认提示
        """
        try:
            return str(obj)
        except Exception:
            return "无法转换的对象"

    def _mask_sensitive(self, text: str, start: int = 3, end: int = 3) -> str:
        """敏感信息脱敏

        对敏感信息进行脱敏处理，只保留开头和结尾的指定字符数。

        Args:
            text: 需要脱敏的文本
            start: 保留开头字符数，默认 3
            end: 保留结尾字符数，默认 3

        Returns:
            str: 脱敏后的文本

        Example:
            >>> self._mask_sensitive("abcdef123456")
            'abc******456'
            >>> self._mask_sensitive("token123", start=2, end=2)
            'to****23'
        """
        if not text or len(text) <= start + end:
            return text
        return text[:start] + '*' * (len(text) - start - end) + text[-end:]

    async def update_config_cookies(self) -> None:
        """更新数据库中的 Cookie 配置

        将当前 cookies_str 持久化到数据库中。
        子类可以覆盖此方法以使用不同的数据库方法。

        Raises:
            捕获所有异常并记录错误日志
        """
        try:
            from db_manager import db_manager
            db_manager.save_cookie(self.cookie_id, self.cookies_str)
            logger.debug(f"【{self.cookie_id}】已更新数据库中的 Cookie")
        except Exception as e:
            logger.error(f"【{self.cookie_id}】更新数据库 Cookie 失败: {self._safe_str(e)}")

    async def _fetch_and_update_cookies(self, response: Any) -> None:
        """从响应中获取并更新 Cookie

        从 HTTP 响应头中提取 set-cookie，更新到内存和数据库。

        Args:
            response: HTTP 响应对象，需包含 headers 属性

        Note:
            只更新响应中返回的新 cookie，保留原有 cookie
        """
        if 'set-cookie' not in response.headers:
            return

        new_cookies = {}
        for cookie in response.headers.getall('set-cookie', []):
            if '=' in cookie:
                name, value = cookie.split(';')[0].split('=', 1)
                new_cookies[name.strip()] = value.strip()

        if new_cookies:
            self.cookies.update(new_cookies)
            self.cookies_str = '; '.join([f"{k}={v}" for k, v in self.cookies.items()])
            await self.update_config_cookies()
            logger.debug("已更新 Cookie 到数据库")

    def get_token(self) -> str:
        """从 cookies 中获取 token

        从 _m_h5_tk cookie 中提取 token 值。

        Returns:
            str: token 值，如果不存在则返回空字符串
        """
        m_h5_tk = trans_cookies(self.cookies_str).get('_m_h5_tk', '')
        if m_h5_tk and '_' in m_h5_tk:
            return m_h5_tk.split('_')[0]
        return ''

    async def refresh_token_if_needed(self, force: bool = False) -> None:
        """按需刷新 token

        检查 token 是否过期，如果过期或强制刷新，则调用刷新回调。

        Args:
            force: 是否强制刷新，默认 False
        """
        if not force and self.current_token and \
           (time.time() - self.last_token_refresh_time) < self.token_refresh_interval:
            return

        old_token = self.get_token()
        logger.info(f"Token 过期或不存在，刷新 token... 当前 _m_h5_tk: {self._mask_sensitive(old_token, 4, 4)}")

        if self.refresh_token:
            await self.refresh_token()

        new_token = self.get_token()
        logger.info(f"Token 刷新完成，新的 _m_h5_tk: {self._mask_sensitive(new_token, 4, 4)}")

    def build_api_params(self, api_name: str, timestamp: Optional[int] = None) -> Dict[str, str]:
        """构建 API 请求参数

        构建闲鱼 API 的基础请求参数。

        Args:
            api_name: API 名称
            timestamp: 时间戳（毫秒），默认使用当前时间

        Returns:
            Dict[str, str]: API 请求参数字典
        """
        return {
            'jsv': API_VERSION,
            'appKey': APP_KEY,
            't': str(timestamp or int(time.time()) * 1000),
            'sign': '',
            'v': '1.0',
            'type': 'originaljson',
            'accountSite': 'xianyu',
            'dataType': 'json',
            'timeout': '20000',
            'api': api_name,
            'sessionOption': 'AutoLoginOnly',
        }

    async def _handle_token_refresh_on_retry(self, attempt: int) -> None:
        """重试时的Token刷新处理

        在重试前刷新Token，确保使用最新的Token。

        Args:
            attempt: 当前重试次数
        """
        old_token = self.get_token()
        logger.info(
            f"【{self.cookie_id}】第{attempt}次重试，强制刷新token... "
            f"当前_m_h5_tk: {self._mask_sensitive(old_token, 4, 4)}"
        )

        if self.refresh_token:
            await self.refresh_token()

        new_token = self.get_token()
        logger.info(
            f"【{self.cookie_id}】Token刷新完成，新的_m_h5_tk: "
            f"{self._mask_sensitive(new_token, 4, 4)}"
        )

    def is_token_error(self, error_msg: str) -> bool:
        """判断错误是否为Token相关错误

        Args:
            error_msg: 错误消息

        Returns:
            bool: 是否为Token错误
        """
        if not error_msg:
            return False
        error_lower = error_msg.lower()
        return 'token' in error_lower or 'sign' in error_lower

    def raise_if_retryable(self, error_msg: str) -> None:
        """根据错误消息抛出可重试异常

        Args:
            error_msg: 错误消息

        Raises:
            TokenExpiredError: 如果是Token相关错误
        """
        if self.is_token_error(error_msg):
            raise TokenExpiredError(error_msg)

    async def _execute_delivery_api(
        self,
        api_name: str,
        order_id: str,
        data_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行发货API请求的公共逻辑

        封装了发货类API请求的通用流程，包括参数构建、签名生成、
        请求发送、响应处理和Cookie更新。

        Args:
            api_name: API名称，如 'mtop.taobao.idle.logistic.consign.dummy'
            order_id: 订单ID
            data_dict: 请求数据字典

        Returns:
            Dict containing success status and order_id or error message

        Raises:
            TokenExpiredError: 当检测到Token相关错误时
            NetworkError: 当发生网络异常时
        """
        if not self.session:
            raise NetworkError("Session未创建")

        # 构建API参数
        params = self.build_api_params(api_name)

        # 序列化数据
        data_val = json.dumps(data_dict)
        data = {'data': data_val}

        # 获取token并生成签名
        token = self.get_token()
        if token:
            logger.info(f"【{self.cookie_id}】使用cookies中的_m_h5_tk token: {self._mask_sensitive(token, 4, 4)}")
        else:
            logger.warning(f"【{self.cookie_id}】cookies中没有找到_m_h5_tk token")

        sign = generate_sign(params['t'], token, data_val)
        params['sign'] = sign

        try:
            logger.info(f"【{self.cookie_id}】开始{api_name}，订单ID: {order_id}")
            api_url = f'https://h5api.m.goofish.com/h5/{api_name}/1.0/'
            async with self.session.post(api_url, params=params, data=data) as response:
                res_json = await response.json()

                await self._fetch_and_update_cookies(response)

                logger.info(f"【{self.cookie_id}】{api_name}响应: {res_json}")

                if res_json.get('ret') and res_json['ret'][0] == 'SUCCESS::调用成功':
                    logger.info(f"【{self.cookie_id}】✅ {api_name}成功，订单ID: {order_id}")
                    return {"success": True, "order_id": order_id}
                else:
                    error_msg = res_json.get('ret', ['未知错误'])[0] if res_json.get('ret') else '未知错误'
                    logger.warning(f"【{self.cookie_id}】❌ {api_name}失败: {error_msg}")

                    # 检查是否为Token错误，如果是则抛出TokenExpiredError触发重试
                    self.raise_if_retryable(error_msg)

                    return {"error": error_msg, "order_id": order_id}

        except (TokenExpiredError, NetworkError):
            raise
        except asyncio.TimeoutError:
            logger.error(f"【{self.cookie_id}】{api_name}请求超时")
            raise NetworkError(f"请求超时")
        except ConnectionError as e:
            logger.error(f"【{self.cookie_id}】{api_name}连接错误: {self._safe_str(e)}")
            raise NetworkError(f"连接错误: {self._safe_str(e)}")
        except Exception as e:
            logger.error(f"【{self.cookie_id}】{api_name} API请求异常: {self._safe_str(e)}")
            raise NetworkError(f"网络异常: {self._safe_str(e)}")
