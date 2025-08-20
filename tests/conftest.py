# tests/conftest.py

import pytest
import yaml
from core import db_handler # 导入我们的 db_handler 模块

# =================================================================
# 1. Pytest 钩子函数 (Hooks)
# =================================================================

def pytest_sessionstart(session):
    """
    在整个测试会话开始时执行一次。
    这是进行全局初始化设置的完美位置。
    """
    # 从 pytest 的配置中获取命令行参数 --env
    env = session.config.getoption("--env")
    if not env:
        pytest.exit("必须通过 --env 参数指定运行环境 (e.g., --env dev)", returncode=1)

    # 调用 db_handler 中的函数来初始化全局数据库会话工厂 (SessionMaker)
    print(f"\n--- Initializing database session for environment: {env} ---")
    db_handler.initialize_session(env)
    print("--- Database session initialized successfully. ---")


def pytest_sessionfinish(session, exitstatus):
    """
    在整个测试会话结束时执行。
    可以在这里进行全局清理工作。
    """
    print("\n--- Tearing down test session. ---")
    # 如果有需要,可以在这里添加关闭连接池等操作
    # db_handler.close_engine() # 假设 db_handler 中有此函数


def pytest_addoption(parser):
    """向 pytest 命令行添加自定义参数"""
    # session 作用域的参数,一次执行中不变
    parser.addoption("--env", action="store", required=True, help="运行环境: dev, staging")

    # test 作用域的参数,用于筛选
    parser.addoption("--component", action="store", default=None, help="按组件筛选用例")
    parser.addoption("--label", action="store", default=None, help="按标签筛选用例")
    parser.addoption("--id", action="store", default=None, help="按ID执行单个用例")

# =================================================================
# 2. Pytest 夹具 (Fixtures)
# =================================================================

@pytest.fixture(scope="session")
def env_config(request):
    """
    加载环境配置的 Fixture,在整个会话中只执行一次。
    注意：这个 Fixture 仍然在 pytest_sessionstart 之后执行。
    """
    env = request.config.getoption("--env")
    with open('configs/config.yaml', 'r') as f:
        configs = yaml.safe_load(f)

    default_config = configs.get('default', {})
    env_specific_config = configs.get(env, {})

    # 合并配置,环境特定配置可以覆盖默认配置
    final_config = {**default_config, **env_specific_config}
    return final_config


@pytest.fixture(scope="session")
def base_url(env_config):
    """从配置中提取 base_url 的 Fixture"""
    url = env_config.get('base_url')
    if not url:
        pytest.fail("配置中未找到 'base_url'")
    return url