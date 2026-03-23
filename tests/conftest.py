"""pytest配置和fixtures"""
import pytest
import tempfile
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    from db_manager import DBManager
    db = DBManager(path)
    yield db
    db.close()
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
