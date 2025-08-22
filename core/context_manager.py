# core/context_manager.py
import re
from jsonpath_ng import parse

class TestContext:
    def __init__(self):
        self.storage = {}

    def set(self, key, value):
        self.storage[key] = value

    def get(self, key):
        return self.storage.get(key)

    def get_variable(self, variable_name):
        """获取已存储的变量值"""
        return self.storage.get(variable_name)

    def set_variable(self, variable_name, value):
        """直接设置变量值"""
        self.storage[variable_name] = value

    def add_step_response(self, step_name, response_data):
        """
        将一个步骤的完整响应数据存入上下文。
        """
        self.storage[step_name] = {'response': response_data}

    def get_value_by_path(self, path_string):
        """
        根据 "response.body" 这样的路径字符串从 context 中取值
        """
        try:
            # 首先检查是否是直接的变量引用
            if '.' not in path_string:
                return self.get_variable(path_string)

            parts = path_string.split('.')
            step_name, source_type, data_source, *json_path_parts = parts

            data = self.storage[step_name][source_type][data_source]

            json_path_expr = parse('.'.join(json_path_parts))
            match = json_path_expr.find(data)

            return match[0].value if match else None
        except (KeyError, IndexError) as e:
            print(f"Error resolving path '{path_string}': {e}")
            return None
    def extract_and_set_variable(self, step_name, variable_name, source, json_path):
        """从指定步骤的响应中提取并设置变量"""
        # source 可能是 'response_body' 或 'response_headers'
        data_source = 'body' if source == 'response_body' else 'headers'

        path_string = f"{step_name}.response.{data_source}.{json_path}"
        value = self.get_value_by_path(path_string)
        if value is None:
            raise ValueError(f"无法从路径 '{path_string}' 提取到值")

        self.set_variable(variable_name, value)
    
    def resolve_placeholders(self, data_structure):
        """递归解析字符串或字典/列表中的占位符 {{...}}"""
        if isinstance(data_structure, str):
            # 匹配 {{response.body.user_id}} 这种模式
            matches = re.findall(r'\{\{([^}]+)\}\}', data_structure)
            for match in matches:
                # 解析路径: step_1.response.body.user_id -> ['step_1', 'response', 'body', 'user_id']
                parts = match.split('.')
                step_name = parts[0]
                source_type = parts[1] # response
                data_source = parts[2] # body or headers
                json_path_expr = '.'.join(parts[3:])
                
                # 从上下文中获取之前步骤的响应
                response_data = self.get(f"{step_name}.{source_type}")
                
                # 使用 jsonpath 提取值
                jsonpath_expression = parse(json_path_expr)
                extracted_value = jsonpath_expression.find(response_data[data_source])[0].value
                
                # 替换占位符
                data_structure = data_structure.replace(f"{{{{{match}}}}}", str(extracted_value))
            return data_structure
        elif isinstance(data_structure, dict):
            return {k: self.resolve_placeholders(v) for k, v in data_structure.items()}
        elif isinstance(data_structure, list):
            return [self.resolve_placeholders(i) for i in data_structure]
        else:
            return data_structure