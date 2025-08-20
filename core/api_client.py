# core/api_client.py

import requests
import allure
from core.context_manager import TestContext
from core.assertion_engine import AssertionEngine
from utils.placeholder_parser import resolve_placeholders

class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.assertion_engine = AssertionEngine()

    def execute_steps(self, case_details):
        """【补全的函数】执行一个用例的所有步骤"""
        context = TestContext()
        case_name = case_details['name']
        all_steps = case_details['steps']

        allure.dynamic.title(f"Case: {case_name}") # Allure 报告显示用例名

        for step in all_steps:
            step_description = step['description']
            step_order = step['step_order']
            step_name = f"step_{step_order}"

            with allure.step(f"Step {step_order}: {step_description}"):
                try:
                    # 1. 解析请求数据中的占位符
                    full_url = self.base_url + resolve_placeholders(step['api_url_path'], context)
                    headers = resolve_placeholders(step['headers'], context)
                    params = resolve_placeholders(step['params'], context)
                    body = resolve_placeholders(step['body'], context)

                    # 记录请求详情到 Allure
                    allure.attach(
                        f"{step['http_method']} {full_url}\nHeaders: {headers}\nParams: {params}\nBody: {body}",
                        name="Request Details",
                        attachment_type=allure.attachment_type.TEXT
                    )

                    # 2. 发送请求
                    response = self.session.request(
                        method=step['http_method'],
                        url=full_url,
                        headers=headers,
                        params=params,
                        json=body
                    )

                    response_data = {
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'body': response.json() if response.content else None
                    }

                    # 记录响应详情到 Allure
                    allure.attach(
                        f"Status Code: {response.status_code}\nHeaders: {response_data['headers']}\nBody: {response_data['body']}",
                        name="Response Details",
                        attachment_type=allure.attachment_type.JSON
                    )

                    # 3. 将完整响应存入上下文
                    context.add_step_response(step_name, response_data)

                    # 4. 执行断言
                    if step['assertions']:
                        self.assertion_engine.execute_assertions(response_data, step['assertions'])

                    # 5. 从响应中提取变量并存入上下文
                    if step['outputs']:
                        for output in step['outputs']:
                            # 此处调用 context 内部的方法来提取并存储变量
                            context.extract_and_set_variable(
                                step_name,
                                output['variable_name'],
                                output['source'],
                                output['json_path']
                            )
                            # 可以在日志或报告中记录提取的变量值
                            extracted_value = context.get_variable(output['variable_name'])
                            allure.attach(f"Extracted '{output['variable_name']}' with value: {extracted_value}", name="Variable Extraction")

                except Exception as e:
                    # 捕获任何异常并标记步骤失败
                    allure.attach(str(e), name="Error Trace", attachment_type=allure.attachment_type.TEXT)
                    raise  # 重新抛出异常,让 Pytest 感知到失败