# Python API Test Framework

一个功能完整的Python API自动化测试框架，支持数据库驱动测试、多环境配置、丰富的断言功能和Allure测试报告。

## 🚀 功能特性

- **数据库驱动测试**：测试用例存储在PostgreSQL数据库中，支持动态生成测试
- **多环境支持**：支持dev、uat等不同环境的配置管理
- **丰富断言**：支持状态码、JSON路径、JSON Schema等多种断言类型
- **参数化测试**：支持从响应中提取变量并在后续步骤中使用
- **Allure报告**：集成Allure测试报告，提供详细的测试结果展示
- **灵活筛选**：支持按组件、标签、用例ID等条件筛选测试用例
- **动态测试生成**：根据数据库中的测试用例自动生成测试函数

## 📁 项目结构

```
auto_test/
├── api/                    # API相关模块
├── configs/               # 配置文件
│   ├── config.yaml       # 主配置文件
│   └── logging_config.yaml # 日志配置
├── core/                  # 核心模块
│   ├── api_client.py     # API客户端
│   ├── assertion_engine.py # 断言引擎
│   ├── context_manager.py # 上下文管理器
│   └── db_handler.py     # 数据库处理器
├── models/               # 数据模型
│   └── tables.py        # 数据库表结构
├── tests/               # 测试文件
│   ├── conftest.py     # pytest配置
│   └── test_main.py    # 主测试文件
├── utils/               # 工具模块
│   └── placeholder_parser.py # 占位符解析器
├── logs/                # 日志文件
├── reports/             # 测试报告
├── requirements.txt     # 依赖包
├── run.py              # 测试运行器
└── README.md           # 项目说明
```

## 🛠️ 快速开始

### 环境要求

- Python 3.8+
- PostgreSQL 数据库
- Allure 命令行工具

### 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖包
pip install -r requirements.txt
```

### 配置环境

1. 复制环境变量模板：
```bash
cp env.example .env
```

2. 编辑 `.env` 文件，配置数据库连接：
```env
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=autotest
DB_USER=admin
```

3. 配置 `configs/config.yaml`：
```yaml
default:
  db_host: "localhost"
  db_port: 5432
  db_user: "admin"

uat:
  base_url: "http://127.0.0.1:8787"
  db_name: "autotest"

dev:
  base_url: "http://api.dev.example.com"
  db_name: "test_db_dev"
```

### 运行测试

```bash
# 运行所有测试
python run.py --env uat

# 直接使用pytest运行
python -m pytest tests/test_main.py -v --env uat

# 查看测试报告
allure open reports/allure-report
```

## 📊 支持的断言类型

- `status_code_equals`: 状态码等于指定值
- `json_path_equals`: JSON路径的值等于指定值
- `json_path_exists`: JSON路径存在
- `contains_text`: 响应体包含指定文本
- `header_equals`: 响应头等于指定值

## 🔧 配置说明

### 数据库表结构

框架使用以下数据库表：
- `api_auto_cases`: 测试用例主表
- `api_actions`: 测试步骤表
- `test_environments`: 测试环境配置
- `test_cases`: 标准测试用例表（兼容）
- `test_steps`: 标准测试步骤表（兼容）
- `test_assertions`: 断言规则表
- `test_step_outputs`: 输出变量规则表

### 环境配置

支持多环境配置，可在 `configs/config.yaml` 中定义不同环境的参数。

### 命令行参数

支持以下pytest参数：
- `--env`: 运行环境（必需）
- `--component`: 按组件筛选
- `--service`: 按服务筛选
- `--module`: 按模块筛选
- `--tags`: 按标签筛选
- `--id`: 按ID执行单个用例
- `--jira`: 按JIRA ID筛选

## 📈 测试报告

框架集成Allure测试报告，提供：
- 详细的测试执行步骤
- 请求和响应信息
- 断言结果
- 失败原因分析
- 美观的HTML界面

## 🎯 使用示例

### 基本测试流程

1. **配置环境**：设置数据库连接和API基础URL
2. **创建测试用例**：在数据库中定义测试用例、步骤和断言
3. **运行测试**：使用 `python run.py --env uat` 执行测试
4. **查看报告**：通过Allure查看详细的测试结果

### 测试用例结构

```yaml
测试用例:
  - 基本信息: 名称、描述、组件、标签
  - 数据变量: 用户名、密码、期望结果等
  - 测试步骤:
    - 登录获取token
    - 使用token查询用户信息
  - 断言规则: 状态码、响应内容验证
  - 输出变量: 提取token等关键信息
```

## 🚨 注意事项

1. **API认证**：确保测试用例中的用户名和密码与目标API匹配
2. **数据库连接**：确保PostgreSQL数据库可访问且表结构正确
3. **环境配置**：确保配置文件中的URL和数据库信息正确
4. **依赖安装**：确保所有Python包和Allure工具已正确安装

## 🔍 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接参数是否正确
   - 确认数据库表是否存在

2. **API认证失败（401错误）**
   - 检查测试用例中的用户名和密码
   - 验证API服务的认证机制
   - 确认API端点是否可访问

3. **测试用例收集失败**
   - 检查pytest参数配置
   - 验证数据库中的测试数据
   - 确认模型映射是否正确

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请通过GitHub Issues联系我们。

