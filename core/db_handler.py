# core/db_handler.py

import os
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from models.tables import TestCase, TestStep # 导入ORM模型


# 加载 .env 文件中的环境变量
load_dotenv()

def load_config(env):
    """根据环境加载YAML配置"""
    with open('configs/config.yaml', 'r') as f:
        configs = yaml.safe_load(f)
    # 合并 default 和指定环境的配置
    env_config = {**configs.get('default', {}), **configs.get(env, {})}
    return env_config

def get_db_engine(env):
    """创建并返回数据库引擎"""
    config = load_config(env)
    db_password = os.getenv("DB_PASSWORD")
    if not db_password:
        raise ValueError("数据库密码未在 .env 文件中设置 (DB_PASSWORD)")

    db_url = (
        f"postgresql+psycopg2://{config['db_user']}:{db_password}@"
        f"{config['db_host']}:{config['db_port']}/{config['db_name']}"
    )
    engine = create_engine(db_url)
    return engine

# --- 数据库查询函数 ---

# 全局 SessionMaker
Session = None

def initialize_session(env):
    """初始化全局 SessionMaker"""
    global Session
    if Session is None:
        engine = get_db_engine(env)
        Session = sessionmaker(bind=engine)

def get_test_cases_by_filter(component=None, label=None, case_id=None):
    """根据筛选条件获取测试用例基本信息"""
    if Session is None:
        raise RuntimeError("数据库会话未初始化. 请先调用 initialize_session(env).")

    with Session() as session:
        query = session.query(TestCase.id, TestCase.name)
        if component:
            query = query.filter(TestCase.component == component)
        if label:
            query = query.filter(TestCase.label == label)
        if case_id:
            query = query.filter(TestCase.id == case_id)

        return query.all()

def get_case_details(case_id):
    """
    【补全的函数】
    获取单个测试用例的完整详细信息,包括所有步骤、断言和输出。
    """
    if Session is None:
        raise RuntimeError("数据库会话未初始化.")

    with Session() as session:
        # 使用 joinedload (Eager Loading) 一次性加载所有关联数据,避免 N+1 查询问题
        test_case = session.query(TestCase).options(
            joinedload(TestCase.steps).joinedload(TestStep.assertions),
            joinedload(TestCase.steps).joinedload(TestStep.outputs)
        ).filter(TestCase.id == case_id).first()

        # 将 SQLAlchemy 对象转换为字典,方便后续处理
        if not test_case:
            return None

        case_details = {
            "id": test_case.id,
            "name": test_case.name,
            "steps": [
                {
                    "id": step.id,
                    "step_order": step.step_order,
                    "description": step.description,
                    "api_url_path": step.api_url_path,
                    "http_method": step.http_method,
                    "headers": step.headers,
                    "params": step.params,
                    "body": step.body,
                    "assertions": [
                        {
                            "rule_type": a.rule_type,
                            "expected_value": a.expected_value,
                            "json_path": a.json_path,
                            "description": a.description
                        } for a in step.assertions
                    ],
                    "outputs": [
                        {
                            "variable_name": o.variable_name,
                            "source": o.source,
                            "json_path": o.json_path
                        } for o in step.outputs
                    ]
                } for step in sorted(test_case.steps, key=lambda s: s.step_order) # 确保步骤有序
            ]
        }
        return case_details