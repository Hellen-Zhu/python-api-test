# models/tables.py

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, JSON,
    ForeignKey, TIMESTAMP, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class TestEnvironment(Base):
    __tablename__ = 'test_environments'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    base_url = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

class TestCase(Base):
    __tablename__ = 'test_cases'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    component = Column(String(100), index=True)
    label = Column(String(100), index=True)
    author = Column(String(50))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # 'TestCase' 对象可以通过 '.steps' 访问其所有关联的 TestStep 对象
    steps = relationship("TestStep", back_populates="case", cascade="all, delete-orphan")

class TestStep(Base):
    __tablename__ = 'test_steps'
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('test_cases.id'), nullable=False)
    step_order = Column(Integer, nullable=False)
    description = Column(Text)
    api_url_path = Column(String(500), nullable=False)
    http_method = Column(String(10), nullable=False)
    headers = Column(JSONB)
    params = Column(JSONB)
    body = Column(JSONB)
    
    case = relationship("TestCase", back_populates="steps")
    assertions = relationship("TestAssertion", back_populates="step", cascade="all, delete-orphan")
    outputs = relationship("TestStepOutput", back_populates="step", cascade="all, delete-orphan")

class TestAssertion(Base):
    __tablename__ = 'test_assertions'
    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('test_steps.id'), nullable=False)
    rule_type = Column(String(50), nullable=False) # e.g., 'status_code_equals', 'json_path_equals'
    expected_value = Column(Text) # 对于JSON Schema断言,这里可以存Schema
    json_path = Column(Text) # 仅在需要路径时使用, e.g., for json_path_equals
    description = Column(Text)
    
    step = relationship("TestStep", back_populates="assertions")
    
class TestStepOutput(Base):
    __tablename__ = 'test_step_outputs'
    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('test_steps.id'), nullable=False)
    variable_name = Column(String(100), nullable=False) # 提取后存储的变量名 (e.g., user_token)
    source = Column(String(50), nullable=False) # 'response_body', 'response_headers'
    json_path = Column(Text, nullable=False)
    
    step = relationship("TestStep", back_populates="outputs")