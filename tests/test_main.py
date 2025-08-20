# tests/test_main.py
import pytest
import allure
from core.db_handler import get_test_cases_by_filter, get_case_details
from core.api_client import ApiClient

# Pytest hook to generate tests dynamically
def pytest_generate_tests(metafunc):
    """
    根据 pytest 命令行的参数 (component, label) 从数据库加载测试用例
    """
    component = metafunc.config.getoption("--component")
    label = metafunc.config.getoption("--label")
    case_id = metafunc.config.getoption("--id")
    
    # 约定：如果运行的是 tests/test_main.py,就根据命令行参数筛选
    # 如果未来有 test_smoke.py, 可以在里面写死 component='smoke'
    if "test_case_data" in metafunc.fixturenames:
        test_cases = get_test_cases_by_filter(component=component, label=label, case_id=case_id)
        # 将从数据库查出的 case 动态注入到测试函数中
        metafunc.parametrize("test_case_data", test_cases, ids=[f"{row[1]}" for row in test_cases])

@allure.epic("API Test Suite")
class TestApi:
    def test_run_case(self, test_case_data, base_url): # base_url 也是一个 fixture
        case_id, case_name = test_case_data

        with allure.step(f"Executing Case ID: {case_id}, Name: {case_name}"):
            # 1. 从数据库获取完整的用例步骤和断言
            full_case_details = get_case_details(case_id)
            if not full_case_details:
                pytest.fail(f"无法找到 Case ID: {case_id} 的详细信息")

            # 2. 初始化 API 客户端
            api_client = ApiClient(base_url)

            # 3. 【修正】按顺序执行所有步骤,传递整个 case_details 字典
            api_client.execute_steps(full_case_details)