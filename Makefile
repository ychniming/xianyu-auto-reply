.PHONY: help install dev test test-cov lint format clean docker-build docker-run

help:
	@echo "闲鱼自动回复系统 - 常用命令"
	@echo ""
	@echo "安装:"
	@echo "  make install        安装生产依赖"
	@echo "  make dev            安装开发依赖"
	@echo ""
	@echo "测试:"
	@echo "  make test           运行所有测试"
	@echo "  make test-unit      运行单元测试"
	@echo "  make test-int       运行集成测试"
	@echo "  make test-cov       运行测试并生成覆盖率报告"
	@echo ""
	@echo "代码质量:"
	@echo "  make lint           运行 ruff 检查"
	@echo "  make format         格式化代码"
	@echo "  make type-check     运行类型检查"
	@echo "  make check          运行所有检查"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   构建 Docker 镜像"
	@echo "  make docker-run     运行 Docker 容器"
	@echo ""
	@echo "清理:"
	@echo "  make clean          清理缓存和临时文件"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio ruff mypy pre-commit
	pre-commit install

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-int:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

test-cov:
	pytest tests/ -v --cov=app --cov=utils --cov-report=html --cov-report=term

lint:
	ruff check .

format:
	ruff format .
	ruff check . --fix

type-check:
	mypy app/ utils/ --ignore-missing-imports

check: lint type-check test

docker-build:
	docker build -f deploy/Dockerfile -t xianyu-auto-reply:latest .

docker-run:
	docker-compose -f deploy/docker-compose.yml up -d

docker-stop:
	docker-compose -f deploy/docker-compose.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml

start:
	python scripts/Start.py

logs:
	tail -f logs/xianyu_*.log
