DO $$
DECLARE
    -- 声明变量来存储新创建记录的 ID
    new_case_id INT;
    step_1_id INT;
    step_2_id INT;
BEGIN

    -- =================================================================
    -- 1. 插入测试用例 (Test Case)
    -- =================================================================
    INSERT INTO test_cases (name, description, component, label, author)
    VALUES (
        'Admin Login and Query User Info',
        'A full integration test for admin login and then querying user data.',
        'User Authentication',
        'Smoke',
        'Test Architect'
    ) RETURNING id INTO new_case_id; -- 将新生成的用例ID存入变量 new_case_id


    -- =================================================================
    -- 2. 插入步骤1：用户登录 (Login)
    -- =================================================================
    INSERT INTO test_steps (case_id, step_order, description, api_url_path, http_method, headers, body)
    VALUES (
        new_case_id,
        1, -- 这是第 1 步
        'Admin user login to get access token',
        '/dar/user/login',
        'POST',
        '{"Content-Type": "application/json"}', -- Headers in JSONB format
        '{"username": "admin", "password": "admin123"}' -- Body in JSONB format
    ) RETURNING id INTO step_1_id; -- 将新生成的步骤ID存入变量 step_1_id


    -- -----------------------------------------------------------------
    -- 3. 为步骤1添加断言 (Assertions)
    -- -----------------------------------------------------------------
    INSERT INTO test_assertions (step_id, rule_type, expected_value, description)
    VALUES
        (step_1_id, 'status_code_equals', '200', 'Verify login is successful (HTTP 200)');


    -- -----------------------------------------------------------------
    -- 4. 为步骤1添加输出提取规则 (Outputs)
    -- -----------------------------------------------------------------
    INSERT INTO test_step_outputs (step_id, variable_name, source, json_path)
    VALUES
        (step_1_id, 'admin_token', 'response_body', 'data.token'); -- 从响应体中提取 access_token 字段，并将其存为变量 'admin_token'


    -- =================================================================
    -- 5. 插入步骤2：查询用户信息 (Query User)
    -- =================================================================
    INSERT INTO test_steps (case_id, step_order, description, api_url_path, http_method, headers, body)
    VALUES (
        new_case_id,
        2, -- 这是第 2 步
        'Query admin user details using the token',
        '/dar/user/queryUser',
        'POST',
        '{"Content-Type": "application/json", "Authorization": "Bearer {{admin_token}}"}',
        '{"username": "admin"}'
    ) RETURNING id INTO step_2_id; -- 将新生成的步骤ID存入变量 step_2_id


    -- -----------------------------------------------------------------
    -- 6. 为步骤2添加断言 (Assertions)
    -- -----------------------------------------------------------------
    INSERT INTO test_assertions (step_id, rule_type, expected_value, json_path, description)
    VALUES
        (step_2_id, 'status_code_equals', '200', NULL, 'Verify query is successful (HTTP 200)'), -- 为 json_path 添加了 NULL
        (step_2_id, 'json_path_equals', 'admin', 'data[0].username', 'Verify the username in response is "admin"');
END $$;