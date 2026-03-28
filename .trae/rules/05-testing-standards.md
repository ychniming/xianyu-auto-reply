# 测试标准

## 5.1 测试类型

| 测试类型 | 覆盖率要求 | 说明 |
|---------|-----------|------|
| 单元测试 | ≥80% | 测试单个函数/方法 |
| 集成测试 | ≥60% | 测试模块间交互 |
| 端到端测试 | 核心流程 | 测试完整业务流程 |
| 性能测试 | 关键接口 | 响应时间、并发能力 |
| AI辅助测试 | 可选 | 智能生成测试用例 |

---

## 5.2 测试框架工具

| 工具 | 用途 | 版本要求 |
|------|------|---------|
| pytest | 测试运行器 | ≥8.0.0 |
| pytest-xdist | 并行测试 | ≥3.5.0 |
| pytest-cov | 覆盖率报告 | ≥4.1.0 |
| pytest-html | HTML报告 | ≥4.1.0 |
| allure-pytest | Allure报告 | ≥2.13.0 |
| pytest-asyncio | 异步测试 | ≥0.23.0 |

---

## 5.3 测试目录结构

```
tests/
├── conftest.py              # pytest配置和fixtures
├── run_tests.py             # 测试运行脚本
├── unit/                    # 单元测试
│   ├── test_utils.py        # 工具函数测试
│   └── test_repositories.py # Repository层测试
├── integration/             # 集成测试
│   └── test_api.py          # API端点测试
├── performance/              # 性能测试
│   └── test_benchmarks.py   # 性能基准测试
├── e2e/                     # 端到端测试
│   └── test_playwright_e2e.py # Playwright E2E测试
├── ai/                      # AI辅助测试
│   └── test_ai_assistant.py # AI测试助手
└── reports/                 # 测试报告输出
```

---

## 5.4 pytest配置

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
markers =
    asyncio: mark test as async test
    unit: mark test as unit test
    integration: mark test as integration test
    e2e: mark test as end-to-end test
    performance: mark test as performance test
    slow: mark test as slow running
    ai: mark test as AI-assisted test
addopts =
    -v
    --tb=short
    --strict-markers
    --html=reports/report.html
    --self-contained-html
    --alluredir=reports/allure-results
    -n auto
```

---

## 5.5 测试标记 (Markers)

| 标记 | 用途 | 示例 |
|------|------|------|
| `@pytest.mark.unit` | 单元测试 | 工具函数、Repository方法 |
| `@pytest.mark.integration` | 集成测试 | API端点、模块交互 |
| `@pytest.mark.e2e` | 端到端测试 | Playwright浏览器测试 |
| `@pytest.mark.performance` | 性能测试 | 响应时间、并发能力 |
| `@pytest.mark.slow` | 慢速测试 | 需要长时间运行的测试 |
| `@pytest.mark.ai` | AI辅助测试 | 智能测试用例生成 |

---

## 5.6 测试执行命令

```bash
# 安装测试依赖
pip install pytest-xdist pytest-cov pytest-html allure-pytest pytest-asyncio

# 运行所有测试（并行）
pytest tests/ -n auto

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行性能测试
pytest tests/performance/ -v -m "slow or performance"

# 运行E2E测试
pytest tests/e2e/ -v -m "e2e"

# 运行带覆盖率
pytest tests/unit/ --cov=app --cov-report=html

# 生成HTML报告
pytest tests/ --html=reports/report.html --self-contained-html

# 生成Allure报告
allure serve reports/allure-results
```

---

## 5.7 测试报告

| 报告类型 | 位置 | 说明 |
|---------|------|------|
| HTML报告 | `reports/report.html` | pytest-html生成 |
| Allure报告 | `reports/allure-results/` | allure-pytest生成 |
| 覆盖率报告 | `htmlcov/` | pytest-cov生成 |
