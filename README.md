# Python API Test Framework

一个功能完整的Python API自动化测试框架，支持数据库驱动测试、多环境配置、丰富的断言功能和Allure测试报告。

## 🚀 功能特性

- **数据库驱动测试**：测试用例存储在PostgreSQL数据库中，支持动态生成测试
- **多环境支持**：支持dev、uat等不同环境的配置管理
- **丰富断言**：支持状态码、JSON路径、JSON Schema、数据库验证等多种断言类型
- **参数化测试**：支持从响应中提取变量并在后续步骤中使用
- **Allure报告**：集成Allure测试报告，提供详细的测试结果展示
- **灵活筛选**：支持按组件、标签、用例ID、JIRA ID等条件筛选测试用例
- **动态测试生成**：根据数据库中的测试用例自动生成测试函数
- **数据库验证**：支持API响应与数据库数据的对比验证
- **自动化备份**：内置数据库备份脚本，支持定时备份和清理

## 📁 项目结构

```
auto_test/
├── api.py                 # FastAPI TaaS服务
├── core/                  # 核心模块
│   ├── api_client.py     # API客户端和执行引擎
│   ├── assertion_engine.py # 智能断言引擎
│   ├── context_manager.py # 测试上下文管理器
│   ├── db_handler.py     # 数据库处理器
│   └── result_writer.py  # 结果写入器
├── models/               # 数据模型
│   └── tables.py        # 数据库表结构
├── tests/               # 测试文件
│   ├── conftest.py     # pytest配置和fixtures
│   └── test_main.py    # 主测试文件
├── utils/               # 工具模块
│   └── placeholder_parser.py # 占位符解析器
├── database/            # 数据库相关
│   ├── create.sql      # 建表脚本
│   ├── insert.sql      # 示例数据
│   └── backups/        # 数据库备份目录
├── logs/                # 日志文件
├── reports/             # 测试报告
│   ├── allure-results/ # Allure原始结果
│   └── allure-report/  # Allure HTML报告
├── requirements.txt     # 依赖包
├── run.py              # 测试运行器
├── back.sh             # 数据库备份脚本
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
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖包
pip install -r requirements.txt
```

### 配置环境

1. 创建 `.env` 文件，配置数据库连接：
```env
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=autotest
DB_USER=admin
```

2. 初始化数据库：
```bash
# 连接到PostgreSQL数据库
psql -U admin -d autotest

# 执行建表脚本
\i database/create.sql

# 插入示例数据（可选）
\i database/insert.sql
```

### 运行测试

```bash
# 运行所有测试
python run.py --env uat

# 按条件筛选运行
python run.py --env uat --service "User Management" --tags "P0,smoke"
python run.py --env uat --jira "PROJ-456"
python run.py --env uat --id 123

# 直接使用pytest运行
python -m pytest tests/ --env uat

# 查看测试报告
allure open reports/allure-report
```

## 📊 支持的断言类型

### 基础断言
- `expectedStatusCode`: 状态码等于指定值
- `body`: JSON响应体部分匹配
- `containsText`: 响应体包含指定文本
- `notNull`: JSON路径存在且不为空
- `notExist`: JSON路径不存在

### 高级断言
- `dbValidation`: 数据库验证
  - `query`: SQL查询语句
  - `expected`: 期望的静态结果
  - `expectedFromResponse`: 从API响应中获取期望值

## 🔧 配置说明

### 数据库表结构

框架使用以下核心数据库表：
- `api_auto_cases`: 测试用例主表
- `api_actions`: 测试步骤表
- `shared_actions`: 共享动作模板表
- `case_data_sets`: 用例数据集表
- `test_environments`: 测试环境配置表
- `auto_progress`: 测试执行进度表

### 环境配置

支持多环境配置，可在 `test_environments` 表中定义不同环境的参数：
```sql
INSERT INTO test_environments (name, base_url, description) 
VALUES ('uat', 'http://api.uat.example.com', 'UAT环境');
```

### 命令行参数

支持以下筛选参数：
- `--env`: 运行环境（必需）
- `--service`: 按服务筛选
- `--module`: 按模块筛选
- `--component`: 按组件筛选
- `--tags`: 按标签筛选（多个用逗号隔开）
- `--jira`: 按JIRA ID筛选
- `--id`: 按用例模板ID执行
- `--debug-mode`: 开启Debug模式

## 🗄️ 数据库备份

### 自动备份

项目内置数据库备份脚本，支持：
- 自动创建备份目录
- 时间戳命名备份文件
- 自动清理7天前的旧备份
- 详细的备份日志

```bash
# 执行备份
./back.sh

# 备份文件位置
./database/backups/autotest-YYYY-MM-DD_HHMMSS.backup
```

### 手动备份

```bash
# 使用pg_dump手动备份
pg_dump -U admin -d autotest -F c -f backup_file.backup

# 恢复备份
pg_restore -U admin -d autotest backup_file.backup
```

## 📈 测试报告

框架集成Allure测试报告，提供：
- 详细的测试执行步骤
- 请求和响应信息
- 断言结果和失败分析
- 数据库验证结果
- 美观的HTML界面
- 支持导出为PDF

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

### 数据库验证示例

```json
{
  "dbValidation": {
    "query": "SELECT user_id, status FROM users WHERE email = '{{@email}}'",
    "expectedFromResponse": {
      "user_id": "{{response.body.userId}}",
      "status": "{{response.body.status}}"
    }
  }
}
```

## 🚨 注意事项

1. **API认证**：确保测试用例中的用户名和密码与目标API匹配
2. **数据库连接**：确保PostgreSQL数据库可访问且表结构正确
3. **环境配置**：确保配置文件中的URL和数据库信息正确
4. **依赖安装**：确保所有Python包和Allure工具已正确安装
5. **备份策略**：定期执行数据库备份，保护测试数据

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

4. **备份失败**
   - 检查PostgreSQL客户端工具是否安装
   - 验证数据库用户权限
   - 确认备份目录权限

### 调试模式

使用 `--debug-mode` 参数开启详细日志：
```bash
python run.py --env uat --debug-mode
```

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请通过GitHub Issues联系我们。