# core/api_client.py

import requests
import allure
import json
from typing import Dict, Any

from core.context_manager import TestContext
from core.assertion_engine import AssertionEngine
from utils.placeholder_parser import resolve_placeholders



class ApiClient:
    """
    API 客户端，是框架的执行引擎。
    负责驱动测试流程：解析参数、发送请求、调用断言、提取变量，并生成详细报告。
    """
    def __init__(self, base_url: str):
        """
        初始化客户端。

        :param base_url: API的基础URL，从环境中获取。
        """
        if not base_url:
            raise ValueError("API base_url 不能为空")
        self.base_url = base_url
        self.session = requests.Session()
        self.assertion_engine = AssertionEngine()
        self.audit_trail = [] # 用于存储本次用例执行的审计轨迹

    def execute_steps(self, case_details: Dict[str, Any], app_db_conn=None):
        """
        执行一个测试用例模板下的所有步骤，并应用正确的验证覆盖逻辑。

        :param case_details: 从 db_handler.get_case_details 获取的完整用例信息。
        :param app_db_conn: (可选) 到被测应用数据库的连接。
        """
        context = TestContext()
        data_set_variables = case_details.get('data_set_variables', {})
        validations_override = case_details.get('validations_override') or {}
        case_name = case_details.get('name', 'Unknown Case')
        all_steps = case_details.get('steps', [])

        allure.dynamic.title(case_name)

        for step in all_steps:
            step_order = step.get('step_order')
            step_description = step.get('description', f'Step {step_order}')
            step_name = f"step_{step_order}"

            with allure.step(f"Step {step_order}: {step_description}"):
                step_status = 'passed'
                request_details_dict = {}
                response_data = {}

                try:
                    # 1. 解析请求数据中的所有占位符
                    api_url_path = resolve_placeholders(step.get('api_url_path', ''), context, data_set_variables)
                    full_url = self.base_url + api_url_path
                    headers = resolve_placeholders(step.get('headers'), context, data_set_variables)
                    params = resolve_placeholders(step.get('params'), context, data_set_variables)
                    body = resolve_placeholders(step.get('body'), context, data_set_variables)

                    request_details_dict = {
                        "method": step.get('http_method'), "url": full_url,
                        "headers": headers, "params": params, "body": body
                    }
                    allure.attach(json.dumps(request_details_dict, indent=2, ensure_ascii=False), name="Request Details", attachment_type=allure.attachment_type.JSON)

                    # 2. 发送 HTTP 请求
                    response = self.session.request(
                        method=step.get('http_method'), url=full_url, headers=headers,
                        params=params, json=body, timeout=30
                    )

                    # 3. 标准化响应数据
                    response_body = None
                    try:
                        response_body = response.json()
                    except json.JSONDecodeError:
                        response_body = response.text
                    response_data = {'status_code': response.status_code, 'headers': dict(response.headers), 'body': response_body}

                    allure.attach(json.dumps(response_data, indent=2, ensure_ascii=False), name="Response Details", attachment_type=allure.attachment_type.JSON)

                    # 4. 将响应存入上下文
                    context.add_step_response(step_name, response_data)

                    # 5. 决定使用哪个验证规则（覆盖或默认）
                    final_validations = None
                    step_validations_override = validations_override.get(str(step_order))
                    default_validations = step.get('validations')

                    if step_validations_override is not None:
                        final_validations = step_validations_override
                        source_message = "Using validation rules from 'case_data_sets' (override)."
                    else:
                        final_validations = default_validations
                        source_message = "Using default validation rules from 'api_actions' or 'shared_actions'."

                    # 6. 执行断言
                    if final_validations:
                        allure.attach(source_message, name="Validation Source")
                        
                        print(f"INFO: {source_message}")

                        # 将原始的验证规则和解析所需的上下文一起传递给断言引擎
                        self.assertion_engine.execute_assertions(
                            response_data,
                            final_validations,
                            app_db_conn=app_db_conn,
                            context=context,
                            data_set_vars=data_set_variables
                        )

                    # 7. 提取并存储输出变量
                    outputs = step.get('outputs')
                    if outputs:
                        for output in outputs:
                            variable_name = output.get('variable_name')
                            if not variable_name: continue

                            context.extract_and_set_variable(
                                step_name, variable_name, output.get('source'), output.get('json_path')
                            )
                            extracted_value = context.get_variable(variable_name)
                            allure.attach(f"Extracted '{variable_name}' with value: {json.dumps(extracted_value)}", name="Variable Extraction", attachment_type=allure.attachment_type.TEXT)

                except Exception as e:
                    step_status = 'failed'
                    allure.attach(f"An error occurred during step execution:\n{type(e).__name__}: {e}", name="Step Execution Error", attachment_type=allure.attachment_type.TEXT)
                    raise
                finally:
                    # 无论成功失败,都记录审计信息
                    self.audit_trail.append({
                        "step_order": step_order,
                        "action_description": step_description,
                        "request_details": request_details_dict,
                        "response_details": response_data,
                        "step_status": step_status
                    })
