-- 1. 环境配置表
CREATE TABLE test_environments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL, -- 环境名 (e.g., 'dev', 'staging', 'prod')
    base_url VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true
);

-- 2. 测试用例主表
CREATE TABLE test_cases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    component VARCHAR(100), -- 所属组件/模块
    label VARCHAR(100),     -- 标签 (e.g., 'P0', 'smoke', 'regression')
    author VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. API 请求步骤表（核心）
CREATE TABLE test_steps (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES test_cases(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL, -- 集成测试中的执行顺序
    description TEXT,
    api_url_path VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL, -- GET, POST, PUT, DELETE etc.
    headers JSONB, -- 请求头 (e.g., {"Content-Type": "application/json"})
    params JSONB,  -- URL查询参数
    body JSONB,    -- 请求体, 支持动态参数 "body": {"userId": "{{step_1.response.body.id}}"}
    UNIQUE (case_id, step_order)
);

-- 4. 断言规则表
CREATE TABLE test_assertions (
    id SERIAL PRIMARY KEY,
    step_id INTEGER REFERENCES test_steps(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL, -- 'status_code', 'json_path_equals', 'contains_text', 'header_equals'
    expected_value TEXT NOT NULL,
    json_path TEXT, -- 仅当 rule_type 为 json_path_* 时使用
    description TEXT
);

-- 5. 动态参数提取表 (用于集成测试)
CREATE TABLE test_step_outputs (
    id SERIAL PRIMARY KEY,
    step_id INTEGER REFERENCES test_steps(id) ON DELETE CASCADE,
    variable_name VARCHAR(100) NOT NULL, -- 提取后存储的变量名 (e.g., 'user_token')
    source VARCHAR(50) NOT NULL, -- 'response_body', 'response_headers'
    json_path TEXT NOT NULL, -- 从源中提取值的 JSON Path
    UNIQUE (step_id, variable_name)
);