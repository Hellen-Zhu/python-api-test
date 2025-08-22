# api.py (Previously api/main.py)

import subprocess
import uuid
import os
import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# 导入我们的数据库操作模块和ORM模型
import sys
# 当此文件位于项目根目录时,项目根目录就是当前文件所在的目录
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core import db_handler
from models.tables import AutoProgress
from dotenv import load_dotenv

# --- TaaS服务启动时的环境加载逻辑 ---
# TaaS服务现在只加载项目根目录下的唯一 .env 文件,
# 该文件定义了如何连接到中央的测试框架数据库。
try:
    dotenv_path = os.path.join(project_root, '.env')
    if os.path.exists(dotenv_path):
        print(f"--- TaaS: Loading environment variables from: {dotenv_path} ---")
        load_dotenv(dotenv_path=dotenv_path)
    else:
        # 如果找不到 .env 文件,服务将无法连接数据库,直接抛出异常
        raise FileNotFoundError(f"启动TaaS服务失败: 找不到根目录下的 .env 配置文件。")

    db_handler.initialize_session()
    print("--- TaaS: Database session initialized successfully. ---")
except Exception as e:
    print(f"--- TaaS FATAL ERROR: Could not initialize database session: {e} ---")
    # 在生产环境中,这里应该让应用进程退出
    exit(1)


app = FastAPI(
    title="API Automation Test as a Service",
    description="一个用于远程触发、监控自动化测试的API服务",
    version="2.0"
)

# =================================================================
# 1. API 模型定义 (Pydantic Models)
# =================================================================

class TestRunRequest(BaseModel):
    """
    触发测试运行的请求体。
    为所有可选字段设置了默认值 None,以实现智能过滤。
    """
    env: str = Field(..., description="运行环境, e.g., 'dev', 'uat'")
    service: Optional[str] = Field(None, description="按服务筛选")
    module: Optional[str] = Field(None, description="按模块筛选")
    component: Optional[str] = Field(None, description="按组件筛选")
    tags: Optional[str] = Field(None, description="按标签筛选, e.g., 'P0,smoke'")
    jira: Optional[str] = Field(None, description="按Jira ID筛选")
    id: Optional[int] = Field(None, description="按用例模板ID筛选")
    debug_mode: Optional[bool] = Field(False, description="是否开启Debug模式")


class TestRunResponse(BaseModel):
    """触发测试后的响应体"""
    message: str
    run_id: str
    status_url: str

class RunStatusResponse(BaseModel):
    """查询测试状态的响应体"""
    run_id: str
    status: Optional[str] = None
    total_cases: Optional[int] = None
    passes: Optional[int] = None
    failures: Optional[int] = None
    skips: Optional[int] = None
    begin_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    allure_report_url: Optional[str] = None # 假设的报告URL

# =================================================================
# 2. 后台任务执行函数
# =================================================================

def execute_pytest_in_background(run_id: str, command: list):
    """在后台线程中执行 pytest 命令,并更新数据库状态"""

    # 更新状态为 RUNNING
    try:
        with db_handler.Session() as session:
            progress_record = session.query(AutoProgress).filter_by(runid=run_id).first()
            if progress_record:
                progress_record.task_status = 'RUNNING'
                progress_record.begin_time = datetime.datetime.now()
                session.commit()
    except Exception as e:
        print(f"Error updating status to RUNNING for run_id {run_id}: {e}")

    # 执行测试
    process = subprocess.Popen(
        command,
        cwd=project_root, # 在项目根目录下执行
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()

    # 测试结束后,conftest.py 中的 sessionfinish 钩子会自动更新最终状态
    # 这里可以打印日志用于调试
    print(f"--- Test run {run_id} finished ---")
    print(f"STDOUT:\n{stdout}")
    if stderr:
        print(f"STDERR:\n{stderr}")


# =================================================================
# 3. API 端点 (Endpoints)
# =================================================================

@app.post("/run-tests/", response_model=TestRunResponse, status_code=202)
async def trigger_test_run(request: TestRunRequest, background_tasks: BackgroundTasks):
    """
    触发一次新的自动化测试运行。
    这是一个异步接口,会立即返回一个 run_id 供后续查询。
    """
    run_id = str(uuid.uuid4())

    # 智能构建命令行参数,忽略占位符
    command = ['python', 'run.py']
    # 定义需要忽略的、由API工具自动生成的占位符值
    placeholders_to_ignore = ["string", 0]

    for field, value in request.model_dump().items():
        # 增加一个条件：忽略无意义的占位符值
        if value is not None and value is not False and value not in placeholders_to_ignore:
            arg_name = f"--{field.replace('_', '-')}"
            if isinstance(value, bool) and value is True:
                command.append(arg_name)
            else:
                command.extend([arg_name, str(value)])

    # 在数据库中预创建一条 PENDING 记录
    try:
        with db_handler.Session() as session:
            progress_record = AutoProgress(
                runid=run_id,
                task_status='PENDING',
                profile=request.env,
                label=request.tags,
                component=request.component,
                run_by='TaaS_API',
                update_time=datetime.datetime.now()
            )
            session.add(progress_record)
            session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create progress record in database: {e}")

    # 使用 FastAPI 的 BackgroundTasks 来安全地执行后台任务
    background_tasks.add_task(execute_pytest_in_background, run_id, command)

    return {
        "message": "Test run accepted and scheduled.",
        "run_id": run_id,
        "status_url": app.url_path_for("get_run_status", run_id=run_id)
    }

