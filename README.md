# Enterprise-Grade API Automation Testing Framework

一个基于 Python 技术栈构建的高度灵活、数据驱动的企业级API自动化测试框架。该框架将"测试逻辑"、"测试流程"与"测试数据"彻底分离，旨在提升测试用例的可维护性、复用性和扩展性。

## 🚀 核心特性

### ✨ 完全数据驱动

- 所有测试元素（环境、用例、步骤、参数、断言）均存储于数据库（PostgreSQL）
- 配置即测试，无需编写代码即可创建和管理测试用例

### 🏗️ 分层用例管理

- 通过 `Service -> Module -> Component` 的结构化层级组织测试用例
- 支持大规模测试用例的清晰分类和管理

### 🔍 强大的筛选与执行

- 支持通过命令行按服务、模块、组件、标签、Jira ID等任意维度动态筛选
- 灵活的测试执行策略，支持并行执行

### 🔄 动作/步骤复用

- 通过"共享动作"(shared_actions)机制实现公共操作的一次定义、处处引用
- 遵循DRY原则，极大提升用例可维护性

### 📊 高级参数化

- 测试模板与数据集分离，轻松实现同一业务流程的多场景、多数据覆盖
- 支持为特定场景定义独特的期望结果

### ✅ 统一关键字驱动断言引擎

- 验证规则采用统一的JSON对象格式
- 支持状态码、响应体匹配、文本包含、JSONPath验证等多种断言方式
- 兼具易用性与强大的功能性

### 📈 企业级报告

- 深度集成Allure，为每个步骤、请求、响应、断言、变量提取生成详细报告
- 层级清晰的测试执行轨迹

### 🌐 测试即服务 (TaaS)

- 内置FastAPI服务，可通过API调用来远程触发测试任务

### 🌍 灵活的环境管理

- 支持多套测试环境（dev、uat）的无缝切换

## 🏗️ 项目架构

```
auto_test/
├── api/                  # TaaS服务 (FastAPI)
├── core/                 # 核心逻辑
│   ├── api_client.py     # API客户端和执行引擎
│   ├── assertion_engine.py # 断言引擎
│   ├── context_manager.py # 测试上下文管理
│   ├── db_handler.py     # 数据库操作
│   └── result_writer.py  # 结果写入
├── models/               # SQLAlchemy ORM模型
│   └── tables.py         # 数据库表结构定义
├── tests/                # Pytest测试文件
│   ├── conftest.py       # Pytest配置
│   └── test_main.py      # 主测试文件
├── utils/                 # 工具类
│   └── placeholder_parser.py # 占位符解析器
├── database/              # 数据库相关文件
├── logs/                  # 日志文件
├── reports/               # Allure报告目录
├── requirements.txt       # 项目依赖
├── run.py                 # 命令行执行入口
└── .env                   # 环境变量配置
```

## 🗄️ 数据库设计

### 核心表结构

#### `api_auto_cases` - 测试用例模板

- 定义测试流程的宏观属性（名称、服务、模块、组件等）
- 支持标签分类和作者信息

#### `case_data_sets` - 数据集

- 为每个用例模板提供具体的测试数据
- 支持变量注入和验证规则覆盖
- 可关联Jira ID实现需求追溯

#### `api_actions` - 测试步骤

- 定义具体的API请求步骤
- 支持引用共享动作模板
- 包含请求参数、验证规则和输出提取

#### `shared_actions` - 共享动作模板

- 存储可复用的公共操作（如登录、认证等）
- 一次定义，多处引用

#### `test_environments` - 测试环境

- 管理不同环境的配置信息
- 支持环境特定的数据库连接

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd auto_test

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库配置

```bash
# 创建.env文件
cp .env.example .env

# 编辑.env文件，配置数据库连接信息
DB_HOST=localhost
DB_PORT=5432
DB_NAME=test_framework
DB_USER=your_username
DB_PASSWORD=your_password
```

### 3. 数据库初始化

```sql
-- 执行SQL脚本创建表结构
-- 参考 models/tables.py 中的表定义
```

### 4. 运行测试

```bash
# 运行所有测试
python run.py

# 按服务筛选
python run.py --service "User Management"

# 按标签筛选
python run.py --tags "P0,smoke"

# 按Jira ID筛选
python run.py --jira "PROJ-456"

# 指定环境
python run.py --env staging

# 并行执行
python run.py --parallel 4
```

## 📝 使用指南

### 创建测试用例

#### 1. 定义共享动作（可选）
```sql
INSERT INTO shared_actions (name, description, api_url_path, http_method, headers, body, validations) 
VALUES (
    'user_login',
    '用户登录操作',
    '/api/auth/login',
    'POST',
    '{"Content-Type": "application/json"}',
    '{"username": "{{username}}", "password": "{{password}}"}',
    '{"expectedStatusCode": 200, "containsText": "token"}'
);
```

#### 2. 创建测试用例模板
```sql
INSERT INTO api_auto_cases (name, service, module, component, tags) 
VALUES (
    '用户注册流程测试',
    'User Management',
    'Authentication',
    'Registration',
    ARRAY['P0', 'smoke']
);
```

#### 3. 定义测试步骤
```sql
INSERT INTO api_actions (case_id, step_order, description, api_url_path, http_method, headers, body, validations) 
VALUES (
    1, 1, '用户注册',
    '/api/users/register',
    'POST',
    '{"Content-Type": "application/json"}',
    '{"username": "{{username}}", "email": "{{email}}", "password": "{{password}}"}',
    '{"expectedStatusCode": 201, "notNull": ["$.id", "$.username"]}'
);
```

#### 4. 创建数据集
```sql
INSERT INTO case_data_sets (case_id, data_set_name, variables, validations_override, jira_id) 
VALUES (
    1, '正常注册场景',
    '{"username": "testuser", "email": "test@example.com", "password": "password123"}',
    '{"1": {"expectedStatusCode": 201, "containsText": "success"}}',
    'PROJ-123'
);
```

### 高级功能

#### 变量注入和上下文
- 使用 `{{@variable_name}}` 引用数据集中的变量
- 使用 `{{step_name.field}}` 引用之前步骤的响应数据

#### 验证规则覆盖
- 在数据集中通过 `validations_override` 字段覆盖默认验证规则
- 支持步骤级别的验证规则定制

#### 并行执行
```bash
# 使用所有可用CPU核心
python run.py --parallel auto

# 指定进程数
python run.py --parallel 8
```

## 📊 测试报告

### Allure报告
- 自动生成详细的测试执行报告
- 包含每个步骤的请求/响应详情
- 支持测试结果的历史趋势分析

### 报告查看
```bash
# 启动Allure服务（自动打开浏览器）
python run.py

# 生成静态报告
allure generate reports/allure-results -o reports/allure-report --clean
```

## 🔧 配置选项

### 环境变量
- `TEST_ENV`: 测试环境名称
- `PYTEST_PARALLEL_WORKERS`: 并行执行的工作进程数

### 命令行参数
- `--env`: 指定测试环境
- `--service`: 按服务筛选
- `--module`: 按模块筛选
- `--component`: 按组件筛选
- `--tags`: 按标签筛选
- `--jira`: 按Jira ID筛选
- `--id`: 按用例ID执行
- `--parallel`: 并行执行配置
- `--debug-mode`: 调试模式

## 🧪 测试示例

### 基础API测试
```python
# 测试用例会自动从数据库加载并执行
# 无需编写Python代码，完全通过数据库配置驱动
```

### 复杂业务流程测试
```python
# 支持多步骤、多数据集的复杂测试场景
# 通过共享动作实现步骤复用
# 支持条件分支和循环逻辑
```

## 🚧 开发计划

### 短期目标
- [ ] Jira双向集成：测试结束后自动回写结果
- [ ] 前端管理界面：Web界面管理测试用例
- [ ] 性能测试集成：支持Locust压测

### 长期目标
- [ ] 移动端测试支持
- [ ] 微服务测试优化
- [ ] AI驱动的测试用例生成

## 📞 联系方式

- 项目维护者：[Hellen]
- 邮箱：[774804075@qq.com]
- 项目链接：[https://github.com/username/auto_test](https://github.com/username/auto_test)



**注意**: 这是一个企业级的测试框架，建议在生产环境中使用前进行充分的测试和验证。
