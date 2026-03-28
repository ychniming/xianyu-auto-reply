"""pytest配置和fixtures - 增强版"""
import pytest
import tempfile
import os
import sys
from typing import Generator, Dict, Any
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def project_root():
    """项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def reports_dir(project_root):
    """报告目录"""
    reports = os.path.join(project_root, "reports")
    os.makedirs(reports, exist_ok=True)
    return reports


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    from app.repositories import DBManager
    db = DBManager(path)
    yield db
    db.close()
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def temp_db_file():
    """创建临时数据库文件路径"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def sample_cookies():
    """示例Cookie数据"""
    return [
        {"id": "account1", "value": "cookie_value_1"},
        {"id": "account2", "value": "cookie_value_2"},
    ]


@pytest.fixture
def sample_keywords():
    """示例关键词数据"""
    return [
        ("你好", "您好，有什么可以帮您的？"),
        ("价格", "这个价格是最优惠的了"),
        ("发货", "您好，商品已发货，请注意查收"),
    ]


@pytest.fixture
def sample_user(temp_db):
    """创建测试用户"""
    temp_db.users.create_user("testuser", "test@example.com", "password123")
    user = temp_db.users.get_user_by_username("testuser")
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "password": "password123"
    }


@pytest.fixture
def sample_card(temp_db, sample_user):
    """创建测试卡券"""
    card_id = temp_db.cards.create_card(
        name="测试卡券",
        card_type="text",
        text_content="测试内容",
        user_id=sample_user["id"]
    )
    return {"id": card_id, "name": "测试卡券", "type": "text"}


@pytest.fixture
def sample_user_info():
    """示例普通用户信息"""
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": "user"
    }


@pytest.fixture
def sample_admin_info():
    """示例管理员用户信息"""
    return {
        "user_id": 999,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin"
    }


@pytest.fixture
def mock_websocket():
    """模拟WebSocket连接"""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def mock_playwright_page():
    """模拟Playwright页面"""
    page = Mock()
    page.goto = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.inner_text = AsyncMock(return_value="")
    page.inner_html = AsyncMock(return_value="")
    page.query_selector = Mock(return_value=None)
    page.wait_for_selector = AsyncMock()
    page.screenshot = AsyncMock()
    return page


@pytest.fixture
def sample_message():
    """示例消息数据"""
    return {
        "msg_id": "msg_123456",
        "from_nick": "买家用户",
        "from_id": "88888888",
        "content": "这个商品多少钱？",
        "msg_type": "text",
        "create_time": datetime.now().isoformat()
    }


@pytest.fixture
def sample_reply():
    """示例回复数据"""
    return {
        "content": "您好，这个商品价格是99元包邮",
        "image_urls": [],
        "audio_url": None
    }


@pytest.fixture
def sample_api_response():
    """示例API响应"""
    return {
        "code": 0,
        "message": "success",
        "data": {}
    }


@pytest.fixture
def auth_headers(sample_user):
    """认证请求头"""
    import jwt
    token = jwt.encode(
        {"user_id": sample_user["id"], "username": sample_user["username"]},
        "test_secret",
        algorithm="HS256"
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers():
    """管理员认证请求头"""
    import jwt
    token = jwt.encode(
        {"user_id": 999, "username": "admin", "role": "admin"},
        "test_secret",
        algorithm="HS256"
    )
    return {"Authorization": f"Bearer {token}"}
