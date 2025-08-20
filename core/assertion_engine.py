# core/assertion_engine.py
import pytest
from jsonpath_ng import parse

class AssertionEngine:
    
    def execute_assertions(self, response, assertion_rules):
        """
        执行一个步骤的所有断言。
        :param response: dict, 包含 'status_code', 'headers', 'body' 的响应对象
        :param assertion_rules: list, 从数据库获取的断言规则对象列表
        """
        failures = []

        for rule in assertion_rules:
            try:
                rule_type = rule['rule_type']
                expected_value = rule['expected_value']

                if rule_type == 'status_code_equals':
                    self._assert_status_code(response['status_code'], expected_value)

                elif rule_type == 'json_path_equals':
                    self._assert_json_path(response['body'], rule['json_path'], expected_value)

                elif rule_type == 'contains_text':
                    self._assert_contains_text(response['body'], expected_value)

                elif rule_type == 'header_equals':
                    self._assert_header(response['headers'], rule['json_path'], expected_value)

            except AssertionError as e:
                description = rule.get('description') or rule['rule_type']
                failures.append(f"Assertion Failed ({description}): {e}")
                
        if failures:
            # 将所有失败信息合并,通过 pytest.fail 抛出,Allure会完美展示
            pytest.fail("\n".join(failures), pytrace=False)

    def _assert_status_code(self, actual_code, expected_code):
        assert str(actual_code) == str(expected_code), \
            f"Expected status code '{expected_code}', but got '{actual_code}'."

    def _assert_json_path(self, body, json_path, expected_value):
        matches = parse(json_path).find(body)
        assert matches, f"JSONPath '{json_path}' not found in response body."
        
        actual_value = matches[0].value
        # 注意类型转换,从数据库来的 expected_value 是字符串
        expected_value_typed = type(actual_value)(expected_value)
        
        assert actual_value == expected_value_typed, \
            f"Value at JSONPath '{json_path}' did not match. Expected: '{expected_value}', Actual: '{actual_value}'."

    def _assert_contains_text(self, body, expected_text):
        assert body and expected_text in str(body), \
            f"Expected text '{expected_text}' not found in response body."

    def _assert_header(self, headers, header_name, expected_value):
        # header_name 不区分大小写
        actual_value = headers.get(header_name.lower())
        assert actual_value is not None, f"Header '{header_name}' not found in response."
        assert str(actual_value) == str(expected_value), \
            f"Header '{header_name}' did not match. Expected: '{expected_value}', Actual: '{actual_value}'."