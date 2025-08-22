# models/tables.py

from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    ForeignKey, TIMESTAMP, func
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class ApiAutoCase(Base):
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
    __tablename__ = 'case_data_sets'
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('api_auto_cases.id'), nullable=False)
    data_set_name = Column(String(255), nullable=False)
    variables = Column(JSONB, nullable=False)

    # ==========================================================
    # 在这里补上 validations_override 字段的声明
    # ==========================================================
    validations_override = Column(JSONB, nullable=True)
    environments = Column(ARRAY(Text), nullable=True, index=True)

    jira_id = Column(String(50), unique=True)
    tags = Column(ARRAY(Text))
    is_active = Column(Boolean, default=True)
    case = relationship("ApiAutoCase", back_populates="data_sets")

class Environment(Base):
    __tablename__ = 'test_environments'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    base_url = Column(String(255), nullable=False)
    description = Column(Text)
    app_db_connection_string = Column(Text)
    is_active = Column(Boolean, default=True)

class AutoProgress(Base):
    """
    此类映射到您现有的 auto_progress 表,用于存储测试运行的概要信息。
    """
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
    label = Column(String(1000)) # 在我们的框架中对应 tags
    runmode = Column(String(255))
    profile = Column(String(200)) # 在我们的框架中对应 env
    update_time = Column(TIMESTAMP)

class AutoTestAudit(Base):
    """此类映射到新的 auto_test_audit 表结构"""
    __tablename__ = 'auto_test_audit'

    id = Column(Integer, primary_key=True)
    runid = Column(String(50), nullable=False, index=True)
    case_id = Column(Integer, nullable=False, index=True)
    data_set_id = Column(Integer, nullable=False, index=True)
    step_order = Column(Integer)
    action_description = Column(Text)
    request_details = Column(JSONB)
    response_details = Column(JSONB)
    step_status = Column(String(20))
    logged_at = Column(TIMESTAMP(timezone=True), server_default=func.now())