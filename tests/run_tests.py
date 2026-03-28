"""测试运行脚本

提供便捷的测试运行命令
"""
import subprocess
import sys
import os


def run_tests(test_type="all", parallel=True, report=True):
    """运行测试

    Args:
        test_type: 测试类型 (unit, integration, e2e, performance, ai, all)
        parallel: 是否并行运行
        report: 是否生成报告
    """
    cmd = ["pytest"]

    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif test_type == "e2e":
        cmd.append("tests/e2e/")
    elif test_type == "performance":
        cmd.append("tests/performance/")
    elif test_type == "ai":
        cmd.append("tests/ai/")
    else:
        cmd.append("tests/")

    cmd.extend(["-v", "--tb=short"])

    if parallel:
        cmd.extend(["-n", "auto"])

    if report:
        cmd.extend([
            "--html=reports/report.html",
            "--self-contained-html",
            f"--alluredir=reports/allure-results"
        ])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def run_with_coverage():
    """运行测试并生成覆盖率报告"""
    cmd = [
        "pytest",
        "tests/unit/",
        "-v",
        "--cov=app",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "-n", "auto"
    ]

    print(f"Running with coverage: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def generate_allure_report():
    """生成Allure报告"""
    cmd = ["allure", "serve", "reports/allure-results"]
    print(f"Generating Allure report: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def open_html_report():
    """打开HTML报告"""
    report_path = os.path.join(os.path.dirname(__file__), "reports", "report.html")
    if os.path.exists(report_path):
        os.startfile(report_path) if sys.platform == "win32" else os.system(f"open {report_path}")
    else:
        print(f"Report not found at {report_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [unit|integration|e2e|performance|ai|all]")
        sys.exit(1)

    test_type = sys.argv[1]
    run_tests(test_type)
