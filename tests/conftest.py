# tests/conftest.py

import pytest
import uuid
import datetime
import os
from sqlalchemy import create_engine

from core import db_handler
from core import result_writer
from models.tables import Environment
from core.api_client import ApiClient

# =================================================================
# 1. Pytest 钩子函数 (Hooks)
# 负责管理整个测试会话的生命周期
# =================================================================

def is_master_process(session):
    """判断当前是否在 pytest-xdist 的主进程中"""
    return not hasattr(session.config, 'workerinput')

def pytest_sessionstart(session):
    """
    在会话开始时，由主进程负责初始化数据库、确定RUN_ID，并创建初始的总览记录。
    """
    # 只有主进程负责初始化和创建初始记录
    if is_master_process(session):
        session.start_time = datetime.datetime.now()

        run_id_from_cmd = session.config.getoption("--run-id")
        # 将 RUN_ID 附加到 config 对象上，以便所有工作进程都能访问
        session.config.run_id = run_id_from_cmd or str(uuid.uuid4())

        print(f"\n--- Test session started at {session.start_time} (RUN_ID: {session.config.run_id}) ---")
        
        # 在主进程中设置环境变量，让工作进程能够访问
        import os
        os.environ['FRAMEWORK_RUN_ID'] = session.config.run_id

        try:
            # 初始化会话工厂并附加到 config 对象
            session.config.db_session_factory = db_handler.initialize_session()
            print("--- Framework DB session factory initialized successfully. ---")

            # 创建初始的总览记录
            env_info = {
                "env": session.config.getoption("--env"),
                "component": session.config.getoption("--component"),
                "tags": session.config.getoption("--tags"),
            }
            with session.config.db_session_factory() as db_sess:
                result_writer.create_run_progress(db_sess, session.config.run_id, env_info)

        except Exception as e:
            pytest.exit(f"数据库初始化或初始记录创建失败: {e}", returncode=2)

def pytest_sessionfinish(session, exitstatus):
    """在会话结束时，只让主进程负责汇总和更新最终报告"""
    if is_master_process(session):
        end_time = datetime.datetime.now()
        print(f"\n--- Test session finished at {end_time} ---")

        # 确保数据库会话工厂可用
        session_factory = getattr(session.config, 'db_session_factory', None)
        if not session_factory:
            try:
                session_factory = db_handler.initialize_session()
            except Exception as e:
                print(f"\nERROR: Failed to initialize database session in sessionfinish: {e}")
                return

        try:
            with session_factory() as db_sess:
                result_writer.update_run_summary(
                    session=db_sess,
                    run_id=session.config.run_id,
                    end_time=end_time,
                    status="FAILED" if exitstatus != 0 else "PASSED"
                )
        except Exception as e:
            print(f"\nERROR: Failed to update run summary in sessionfinish: {e}")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    在每个测试执行后，由工作进程负责写入单条用例审计，并在Debug模式下写入详细步骤。
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == 'call':
        try:
            run_data = item.callspec.params.get('test_case_run_data')
            if not run_data: return

            case_id, data_set_id, display_name, jira_id = run_data

            # 获取run_id：优先从config，然后从环境变量，最后从命令行参数
            run_id = getattr(item.config, 'run_id', None)
            if not run_id:
                import os
                run_id = os.environ.get('FRAMEWORK_RUN_ID') or item.config.getoption("--run-id", default=None)
            client_instance = item.funcargs.get('api_client')
            session_factory = getattr(item.config, 'db_session_factory', None)
            
            # 如果工作进程中没有会话工厂，重新初始化
            if not session_factory:
                try:
                    session_factory = db_handler.initialize_session()
                    item.config.db_session_factory = session_factory
                except Exception as e:
                    print(f"\nERROR: Failed to initialize session factory in worker: {e}")
                    return

            if run_id and client_instance and session_factory:
                # 获取本次使用的、已解析的变量
                variables = client_instance.resolved_data_set_variables

                with session_factory() as db_sess:
                    # 写入单条用例审计，并获取其ID
                    audit_case_id = result_writer.write_case_audit(
                        db_sess, run_id, case_id, data_set_id, jira_id,
                        display_name, variables, report
                    )

                    # 如果是Debug模式，则写入详细步骤
                    is_debug = item.config.getoption("--debug-mode")
                    if is_debug and audit_case_id and client_instance.audit_trail:
                        result_writer.write_debug_log(
                            db_sess, audit_case_id, client_instance.audit_trail
                        )
        except Exception as e:
            print(f"\nERROR: Failed to write result for item {item.name}: {e}")

def pytest_addoption(parser):
    """向 pytest 命令行注册所有自定义参数"""
    parser.addoption("--env", action="store", required=True, help="指定运行环境: dev, uat")
    parser.addoption("--service", action="store", default=None)
    parser.addoption("--module", action="store", default=None)
    parser.addoption("--component", action="store", default=None)
    parser.addoption("--tags", action="store", default=None)
    parser.addoption("--jira", action="store", default=None)
    parser.addoption("--id", action="store", default=None)
    parser.addoption("--run-id", action="store", default=None)

    parser.addoption("--debug-mode", action="store_true", default=False)

# =================================================================
# 3. Pytest 夹具 (Fixtures)
# 负责为测试函数提供可复用的资源
# =================================================================

@pytest.fixture(scope="session")
def db_session_factory(request):
    """提供一个会话级别的数据库会话工厂"""
    factory = getattr(request.config, 'db_session_factory', None)
    if not factory:
        # 在工作进程中，重新初始化数据库会话工厂
        try:
            factory = db_handler.initialize_session()
            request.config.db_session_factory = factory
        except Exception as e:
            pytest.fail(f"数据库会话工厂初始化失败: {e}")
    return factory

@pytest.fixture(scope="session")
def test_environment(request, db_session_factory):
    """根据 --env 参数，从数据库中加载完整的 Environment 配置对象。"""
    env_name = request.config.getoption("--env")
    with db_session_factory() as session:
        env_config = session.query(Environment).filter(
            Environment.name == env_name, Environment.is_active == True
        ).first()

    if not env_config:
        pytest.fail(f"在 test_environments 表中未找到名为 '{env_name}' 的活动环境配置")

    print(f"--- Running tests against Environment: '{env_name}' ---")
    return env_config

@pytest.fixture(scope="session")
def base_url(test_environment):
    """从 test_environment fixture 中获取 base_url"""
    print(f"--- Using base_url: {test_environment.base_url} ---")
    return test_environment.base_url

@pytest.fixture(scope="session")
def app_db_connection(test_environment):
    """根据当前测试环境，创建并提供一个到被测应用数据库的连接。"""
    conn_string = test_environment.app_db_connection_string
    if not conn_string:
        yield None
        return

    engine, connection = None, None
    try:
        engine = create_engine(conn_string)
        connection = engine.connect()
        print(f"--- Successfully connected to application DB for env '{test_environment.name}' ---")
        yield connection
    except Exception as e:
        pytest.fail(f"无法连接到应用程序数据库: {e}", pytrace=False)
    finally:
        if connection: connection.close()
        if engine: engine.dispose()
        print("\n--- Application DB connection closed. ---")

@pytest.fixture
def api_client(base_url):
    """
    一个函数级别的 fixture，为每个测试用例创建一个独立的 ApiClient 实例。
    """
    return ApiClient(base_url)
