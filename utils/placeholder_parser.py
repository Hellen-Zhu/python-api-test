# utils/placeholder_parser.py

import re
from jsonpath_ng import parse

def find_placeholders(data_structure):
    """递归查找所有占位符,返回一个集合"""
    placeholders = set()
    if isinstance(data_structure, str):
        matches = re.findall(r'\{\{([^}]+)\}\}', data_structure)
        placeholders.update(matches)
    elif isinstance(data_structure, dict):
        for value in data_structure.values():
            placeholders.update(find_placeholders(value))
    elif isinstance(data_structure, list):
        for item in data_structure:
            placeholders.update(find_placeholders(item))
    return placeholders

def resolve_placeholders(data_structure, context):
    """
    用上下文中的实际值替换数据结构中的占位符。
    """
    if isinstance(data_structure, str):
        for placeholder in find_placeholders(data_structure):
            # 假设 placeholder 格式为 "step_1.response.body.id"
            value = context.get_value_by_path(placeholder)
            if value is None:
                raise ValueError(f"Placeholder '{placeholder}' could not be resolved from context.")
            # 注意：简单的replace可能在 '{{token}}' 和 'Bearer {{token}}' 场景下有问题
            # 更健壮的方式是只替换完全匹配的占位符
            data_structure = data_structure.replace(f"{{{{{placeholder}}}}}", str(value))
        return data_structure
    elif isinstance(data_structure, dict):
        return {k: resolve_placeholders(v, context) for k, v in data_structure.items()}
    elif isinstance(data_structure, list):
        return [resolve_placeholders(i) for i in data_structure]
    else:
        return data_structure

# core/context_manager.py
from jsonpath_ng import parse

class TestContext:
    def __init__(self):
        # 存储结构: {'step_1': {'response': {...}}, 'step_2': {'response': {...}}}
        self.storage = {}

    def add_step_response(self, step_name, response_data):
        self.storage[step_name] = {'response': response_data}

    def get_value_by_path(self, path_string):
        """
        根据 "step_1.response.body.user.id" 这样的路径字符串从 context 中取值
        """
        try:
            parts = path_string.split('.')
            step_name, source_type, data_source, *json_path_parts = parts
            
            # 获取数据源 (e.g., response body or headers)
            data = self.storage[step_name][source_type][data_source]
            
            # 使用 jsonpath 提取值
            json_path_expr = parse('.'.join(json_path_parts))
            match = json_path_expr.find(data)
            
            return match[0].value if match else None
        except (KeyError, IndexError) as e:
            print(f"Error resolving path '{path_string}': {e}")
            return None