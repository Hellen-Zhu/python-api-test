# tests/conftest.py

import pytest
import uuid
import datetime
import os

from sqlalchemy import create_engine

from core import db_handler
from core import result_writer
from models.tables import Environment
from core.api_client import ApiClient # 导入 ApiClient 以便在 fixture 中使用

# =================================================================
# 1. 全局变量和统计器 (Global Variables & Statistics Collector)
# =================================================================

# 为每次测试运行生成一个唯一的ID,用于关联所有结果
RUN_ID = str(uuid.uuid4())

# 用于在整个测试会话期间收集统计数据的对象
class TestStatsCollector:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = None
        self.end_time = None

    @property
    def total(self):
        return self.passed + self.failed + self.skipped

# 在会话开始时创建统计器实例
stats_collector = TestStatsCollector()

# =================================================================
# 2. Pytest 钩子函数 (Hooks)
# 负责管理整个测试会话的生命周期
# =================================================================

def pytest_sessionstart(session):
    """在会话开始时,初始化数据库并记录开始时间"""
    stats_collector.start_time = datetime.datetime.now()
    print(f"\n--- Test session started at {stats_collector.start_time} (RUN_ID: {RUN_ID}) ---")

    try:
        db_handler.initialize_session()
        print("--- Database session initialized successfully. ---")
    except Exception as e:
        pytest.exit(f"数据库初始化失败,请检查 .env 文件配置: {e}", returncode=2)

def pytest_sessionfinish(session, exitstatus):
    """在会话结束时,记录结束时间,并写入概要信息到数据库"""
    stats_collector.end_time = datetime.datetime.now()
    print(f"\n--- Test session finished at {stats_collector.end_time} ---")

    # 准备概要数据
    summary_data = {
        "run_id": RUN_ID,
        "start_time": stats_collector.start_time,
        "end_time": stats_collector.end_time,
        "total": stats_collector.total,
        "passed": stats_collector.passed,
        "failed": stats_collector.failed,
        "skipped": stats_collector.skipped,
        "status": "FAILED" if exitstatus != 0 else "PASSED",
        "env": session.config.getoption("--env"),
        "component": session.config.getoption("--component"),
        "tags": session.config.getoption("--tags"),
        "run_by": "pytest" # 兼容不同系统获取用户名
    }

    # 调用写入模块
    result_writer.write_run_summary(summary_data)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    在每个测试的 setup, call, teardown 阶段后执行。
    我们用它来捕获测试结果,更新统计数据,并触发详细日志的写入。
    """
    # 执行原始的钩子函数,获取测试报告
    outcome = yield
    report = outcome.get_result()

    # 统计 passed/failed/skipped 数量
    if report.when == 'call':
        if report.passed:
            stats_collector.passed += 1
        elif report.failed:
            stats_collector.failed += 1
    elif report.skipped and 'call' not in [rep.when for rep in outcome.get_reports()]:
        # 仅当 setup/teardown 失败导致跳过时才计数
        stats_collector.skipped += 1

    # 写入详细审计日志 (如果开启了 debug 模式)
    # 我们只在 'call' 阶段结束后处理,因为它代表了测试用例本身的执行
    if report.when == 'call':
        try:
            is_debug = item.config.getoption("--debug-mode")
            if is_debug:
                run_data = item.callspec.params.get('test_case_run_data')
                client_instance = item.funcargs.get('api_client')

                if run_data and client_instance and client_instance.audit_trail:
                    case_id, data_set_id, _, jira_id = run_data
                    # 注意：此处的 write_audit_log 逻辑需要您在 result_writer.py 中实现
                    # 它需要根据 run_id, case_id, data_set_id 找到 progress_id
                    result_writer.write_audit_log(
                        RUN_ID, case_id, data_set_id, client_instance.audit_trail
                    )
                    print(f"\n[DEBUG MODE] Audit trail captured for case_id={case_id}, data_set_id={data_set_id}. ")

        except Exception as e:
            print(f"\nERROR: Failed to process audit log for item {item.name}: {e}")

def pytest_addoption(parser):
    """向 pytest 命令行注册所有自定义参数"""
    # 环境参数 (强制要求)
    parser.addoption("--env", action="store", required=True,
                     help="指定运行环境: dev, uat")

    # 用例筛选参数 (可选)
    parser.addoption("--service", action="store", default=None, help="按服务筛选用例")
    parser.addoption("--module", action="store", default=None, help="按模块筛选用例")
    parser.addoption("--component", action="store", default=None, help="按组件筛选用例")
    parser.addoption("--tags", action="store", default=None, help="按标签筛选,多个用逗号隔开 (e.g., P0,smoke)")
    parser.addoption("--jira", action="store", default=None, help="按Jira ID筛选用例")
    parser.addoption("--id", action="store", default=None, help="按用例模板ID(case_id)执行其所有数据集")

    # 功能开关 (可选)
    parser.addoption("--debug-mode", action="store_true", default=False,
                     help="开启Debug模式,会将详细审计日志写入数据库")

# =================================================================
# 3. Pytest 夹具 (Fixtures)
# 负责为测试函数提供可复用的资源
# =================================================================

@pytest.fixture(scope="session")
def base_url(request):
    """
    一个会话级别的 fixture,负责根据 --env 参数从数据库的
    test_environments 表中动态获取正确的 API base_url。
    """
    env_name = request.config.getoption("--env")

    if not db_handler.Session:
        pytest.fail("数据库会话未被初始化,无法获取 base_url", pytrace=False)

    url = None
    with db_handler.Session() as session:
        env_config = session.query(Environment).filter(
            Environment.name == env_name,
            Environment.is_active == True
        ).first()

        if env_config:
            url = env_config.base_url

    if not url:
        pytest.fail(f"在数据库的 test_environments 表中未找到名为 '{env_name}' 的活动环境配置", pytrace=False)

    print(f"--- Using base_url for env '{env_name}': {url} ---")
    return url



@pytest.fixture
def api_client(base_url):
    """
    一个函数级别的 fixture,为每个测试用例创建一个独立的 ApiClient 实例。
    这对于隔离测试状态和收集每个用例独立的审计日志至关重要。
    """
    return ApiClient(base_url)

# 核心 Fixture,用于加载当前环境的完整配置
@pytest.fixture(scope="session")
def test_environment(request):
    """
    根据 --env 参数,从数据库中加载完整的 Environment 配置对象。
    """
    env_name = request.config.getoption("--env")

    if not db_handler.Session:
        pytest.fail("数据库会话未被初始化,无法获取环境配置", pytrace=False)

    environment_config = None
    with db_handler.Session() as session:
        environment_config = session.query(Environment).filter(
            Environment.name == env_name,
            Environment.is_active == True
        ).first()

    if not environment_config:
        pytest.fail(f"在数据库 test_environments 表中未找到名为 '{env_name}' 的活动环境配置", pytrace=False)

    print(f"--- Running tests against Environment: '{env_name}' ---")
    return environment_config

# 为被测应用数据库创建连接的 Fixture
@pytest.fixture(scope="session")
def app_db_connection(test_environment):
    """
    根据当前测试环境,创建并提供一个到被测应用数据库的连接。
    在整个测试会话结束后会自动关闭连接。
    """
    conn_string = test_environment.app_db_connection_string
    if not conn_string:
        print("\n--- WARNING: No app_db_connection_string found for this environment. DB validation will be skipped. ---")
        yield None # 如果没有连接字符串,则返回 None
        return

    engine = None
    connection = None
    try:
        engine = create_engine(conn_string)
        connection = engine.connect()
        print(f"--- Successfully connected to application DB for environment '{test_environment.name}' ---")
        yield connection # 将连接对象提供给测试
    except Exception as e:
        pytest.fail(f"无法连接到应用程序数据库: {e}", pytrace=False)
    finally:
        if connection:
            connection.close()
        if engine:
            engine.dispose()
        print("\n--- Application DB connection closed. ---")