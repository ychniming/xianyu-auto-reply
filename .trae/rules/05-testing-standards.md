# 测试标准

[返回主目录](./project_rules.md)

---

## 5.1 测试类型

| 测试类型 | 覆盖率要求 | 说明 |
|---------|-----------|------|
| 单元测试 | ≥80% | 测试单个函数/方法 |
| 集成测试 | ≥60% | 测试模块间交互 |
| 端到端测试 | 核心流程 | 测试完整业务流程 |
| 性能测试 | 关键接口 | 响应时间、并发能力 |

---

## 5.2 单元测试规范

### 测试文件组织

```
tests/
├── unit/                    # 单元测试
│   ├── test_xianyu_utils.py
│   ├── test_message_utils.py
│   ├── test_db_manager.py
│   └── test_cookie_manager.py
├── integration/             # 集成测试
│   ├── test_api.py
│   └── test_websocket.py
├── e2e/                     # 端到端测试
│   └── test_user_flow.py
└── conftest.py              # pytest配置
```

### 测试用例编写

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

class TestCookieManager:
    """CookieManager 单元测试"""
    
    @pytest.fixture
    def manager(self, event_loop):
        """创建测试实例"""
        from cookie_manager import CookieManager
        return CookieManager(event_loop)
    
    def test_add_cookie_success(self, manager):
        """测试添加Cookie成功"""
        cookie_id = "test_account"
        cookie_value = "test_cookie_value"
        
        manager.add_cookie(cookie_id, cookie_value)
        
        assert cookie_id in manager.cookies
        assert manager.cookies[cookie_id] == cookie_value
    
    def test_add_cookie_duplicate(self, manager):
        """测试添加重复Cookie"""
        manager.add_cookie("test", "value1")
        
        with pytest.raises(ValueError, match="already exists"):
            manager.add_cookie("test", "value2")
    
    @pytest.mark.asyncio
    async def test_run_xianyu_success(self, manager):
        """测试启动XianyuLive任务"""
        with patch('XianyuAutoAsync.XianyuLive') as MockLive:
            mock_instance = AsyncMock()
            MockLive.return_value = mock_instance
            
            await manager._run_xianyu("test", "value", 1)
            
            MockLive.assert_called_once()
            mock_instance.main.assert_called_once()
```

### 测试覆盖率配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# coverage配置
[coverage:run]
source = .
omit = 
    tests/*
    venv/*
    */migrations/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

---

## 5.3 测试执行

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/unit/test_cookie_manager.py

# 运行指定测试类
pytest tests/unit/test_cookie_manager.py::TestCookieManager

# 运行指定测试方法
pytest tests/unit/test_cookie_manager.py::TestCookieManager::test_add_cookie_success

# 生成覆盖率报告
pytest --cov=. --cov-report=html

# 运行性能测试
pytest tests/performance/ --benchmark-only
```

---

## 5.4 测试数据管理

```python
# conftest.py
import pytest
import tempfile
import os

@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)

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
```
