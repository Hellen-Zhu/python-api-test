import pytest
import allure
from core.db_handler import get_test_cases_by_filter, get_case_details

def pytest_generate_tests(metafunc):
    if "test_case_run_data" in metafunc.fixturenames:
        # 从 pytest 配置中获取新的参数
        env= metafunc.config.getoption("--env")
        service = metafunc.config.getoption("--service")
        module = metafunc.config.getoption("--module")
        component = metafunc.config.getoption("--component")
        tags = metafunc.config.getoption("--tags")
        jira_id = metafunc.config.getoption("--jira")
        case_id = metafunc.config.getoption("--id")

        test_cases_to_run = get_test_cases_by_filter(
            env=env,
            service=service, module=module, component=component,
            tags=tags, jira_id=jira_id, case_id=case_id
        )
        if not test_cases_to_run:
            pytest.skip("没有根据筛选条件找到任何测试用例")

        metafunc.parametrize(
            "test_case_run_data",
            test_cases_to_run,
            ids=[row[2] for row in test_cases_to_run]
        )

@allure.epic("API Test Suite")
class TestApi:
    def test_run_case(self, test_case_run_data, api_client, app_db_connection):
        case_id, data_set_id, case_display_name, jira_id = test_case_run_data

        with allure.step(f"Executing Case: {case_display_name}"):
            full_case_details = get_case_details(case_id, data_set_id)
            if not full_case_details:
                pytest.fail(f"无法找到 Case ID: {case_id} / DataSet ID: {data_set_id} 的详细信息")

            api_client.execute_steps(full_case_details, app_db_conn=app_db_connection)