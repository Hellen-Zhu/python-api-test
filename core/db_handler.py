# core/db_handler.py

import os
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker, joinedload
from models.tables import ApiAutoCase, CaseDataSet, SharedAction, Environment

def get_db_engine():
    """从环境变量创建并返回数据库引擎。"""
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_NAME', 'DB_PASSWORD']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"数据库连接环境变量 '{var}' 未设置")
    db_url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(db_url, echo=False)

def initialize_session():
    """初始化并返回一个 SQLAlchemy SessionMaker (会话工厂)。"""
    engine = get_db_engine()
    return sessionmaker(bind=engine)

def get_test_cases_by_filter(session, env: str, service=None, module=None, component=None, tags=None, jira_id=None, case_id=None):
    """根据所有筛选条件，获取需要运行的测试场景列表。"""
    query = session.query(
        ApiAutoCase.id,
        CaseDataSet.id,
        ApiAutoCase.name,
        CaseDataSet.data_set_name,
        CaseDataSet.jira_id
    ).join(ApiAutoCase, ApiAutoCase.id == CaseDataSet.case_id).filter(CaseDataSet.is_active == True)

    query = query.filter(
        or_(
            CaseDataSet.environments == None,
            CaseDataSet.environments == [],
            CaseDataSet.environments.any(env)
        )
    )

    if service: query = query.filter(ApiAutoCase.service == service)
    if module: query = query.filter(ApiAutoCase.module == module)
    if component: query = query.filter(ApiAutoCase.component == component)
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
        query = query.filter(ApiAutoCase.tags.contains(tag_list))
    if jira_id: query = query.filter(CaseDataSet.jira_id == jira_id)
    if case_id: query = query.filter(ApiAutoCase.id == case_id)

    results = query.all()
    return [(row[0], row[1], f"{row[2]} [{row[3]}]", row[4]) for row in results]

def get_case_details(session, case_id, data_set_id):
    """获取单个测试场景的完整详细信息。"""
    shared_actions_list = session.query(SharedAction).all()
    shared_actions_map = {sa.name: sa for sa in shared_actions_list}

    test_case = session.query(ApiAutoCase).options(
        joinedload(ApiAutoCase.actions)
    ).filter(ApiAutoCase.id == case_id).first()

    data_set = session.query(CaseDataSet).filter(CaseDataSet.id == data_set_id).first()

    if not test_case or not data_set: return None

    resolved_actions = []
    for action_ref in sorted(test_case.actions, key=lambda a: a.step_order):
        final_action_data = {}
        template = None
        if action_ref.shared_action_ref:
            template = shared_actions_map.get(action_ref.shared_action_ref)
            if not template:
                raise ValueError(f"共享动作 '{action_ref.shared_action_ref}' 未在 shared_actions 表中找到")
            final_action_data = {key: getattr(template, key) for key in template.__dict__ if not key.startswith('_')}
        else:
            final_action_data = {key: getattr(action_ref, key) for key in action_ref.__dict__ if not key.startswith('_')}
        final_action_data["description"] = action_ref.description or (template.description if template else '')
        final_action_data["step_order"] = action_ref.step_order
        resolved_actions.append(final_action_data)

    case_details = {
        "id": test_case.id,
        "name": test_case.name,
        "data_set_variables": data_set.variables,
        "validations_override": data_set.validations_override,
        "steps": resolved_actions
    }
    return case_details
