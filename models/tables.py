# models/tables.py

from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    ForeignKey, TIMESTAMP, func, REAL
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import declarative_base, relationship

# 创建所有ORM类的基类
Base = declarative_base()

# =================================================================
# 1. 测试用例定义相关的表 (Test Case Definition Tables)
# =================================================================

class ApiAutoCase(Base):
    """测试用例模板定义表 (菜谱)"""
    __tablename__ = 'api_auto_cases'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    service = Column(String(100), nullable=False, index=True)
    module = Column(String(100), index=True)
    component = Column(String(100), index=True)
    tags = Column(ARRAY(Text), index=True)
    author = Column(String(50))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    actions = relationship("ApiAction", back_populates="case", cascade="all, delete-orphan")
    data_sets = relationship("CaseDataSet", back_populates="case", cascade="all, delete-orphan")

class ApiAction(Base):
    """测试流程中的具体动作步骤表 (烹饪流程)"""
    __tablename__ = 'api_actions'
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('api_auto_cases.id'), nullable=False)
    step_order = Column(Integer, nullable=False)
    description = Column(Text)
    shared_action_ref = Column(String(100), ForeignKey('shared_actions.name'))
    api_url_path = Column(String(500))
    http_method = Column(String(10))
    headers = Column(JSONB)
    params = Column(JSONB)
    body = Column(JSONB)
    validations = Column(JSONB)
    outputs = Column(JSONB)
    case = relationship("ApiAutoCase", back_populates="actions")

class SharedAction(Base):
    """可复用的共享动作模板库 (食材处理步骤)"""
    __tablename__ = 'shared_actions'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    api_url_path = Column(String(500), nullable=False)
    http_method = Column(String(10), nullable=False)
    headers = Column(JSONB)
    params = Column(JSONB)
    body = Column(JSONB)
    validations = Column(JSONB)
    outputs = Column(JSONB)

class CaseDataSet(Base):
    """参数化用例的数据集表 (点餐单)"""
    __tablename__ = 'case_data_sets'
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('api_auto_cases.id'), nullable=False)
    data_set_name = Column(String(255), nullable=False)
    variables = Column(JSONB, nullable=False)
    validations_override = Column(JSONB, nullable=True)
    environments = Column(ARRAY(Text), nullable=True, index=True)
    jira_id = Column(String(50), unique=True)
    tags = Column(ARRAY(Text))
    is_active = Column(Boolean, default=True)
    case = relationship("ApiAutoCase", back_populates="data_sets")

# =================================================================
# 2. 测试配置相关的表 (Test Configuration Tables)
# =================================================================

class Environment(Base):
    """测试环境配置表"""
    __tablename__ = 'test_environments'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    base_url = Column(String(255), nullable=False)
    app_db_connection_string = Column(Text)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

# =================================================================
# 3. 测试结果记录相关的表 (Test Result Tables)
# =================================================================

class AutoProgress(Base):
    """测试运行的概要信息表"""
    __tablename__ = 'auto_progress'
    id = Column(Integer, primary_key=True)
    runid = Column(String(50))
    version_id = Column(String(35))
    component = Column(String(50))
    total_cases = Column(Integer)
    passes = Column(Integer)
    failures = Column(Integer)
    skips = Column(Integer)
    begin_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    releaseversion = Column(String(200))
    task_status = Column(String(25))
    run_by = Column(String(50))
    label = Column(String(1000))
    runmode = Column(String(255))
    profile = Column(String(200))
    update_time = Column(TIMESTAMP)

class AutoCaseAudit(Base):
    """单个测试场景的详细结果审计表"""
    __tablename__ = 'auto_case_audit'
    id = Column(Integer, primary_key=True)
    runid = Column(String(50), nullable=False, index=True)
    case_id = Column(Integer)
    data_set_id = Column(Integer)
    scenario = Column(Text)
    issue_key = Column(String(50))
    run_status = Column(String(20))
    duration = Column(REAL)
    error_message = Column(Text)
    variables = Column(JSONB)
    update_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    debug_logs = relationship("AutoTestAudit", back_populates="case_audit", cascade="all, delete-orphan")

class AutoTestAudit(Base):
    """Debug模式下每个步骤的详细交互日志表"""
    __tablename__ = 'auto_test_audit'
    id = Column(Integer, primary_key=True)
    audit_case_id = Column(Integer, ForeignKey('auto_case_audit.id'), nullable=False)
    step_order = Column(Integer)
    action_description = Column(Text)
    request_details = Column(JSONB)
    response_details = Column(JSONB)
    step_status = Column(String(20))
    case_audit = relationship("AutoCaseAudit", back_populates="debug_logs")
