# api/main.py
from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import threading

app = FastAPI()

class TestRunRequest(BaseModel):
    env: str
    component: str = None
    label: str = None
    case_id: int = None

def run_tests_in_background(command):
    # 在后台运行 pytest 命令
    subprocess.Popen(command, shell=True)

@app.post("/run-tests/")
async def trigger_test_run(request: TestRunRequest):
    command = f"python ../run.py --env {request.env}"
    if request.component:
        command += f" --component {request.component}"
    if request.label:
        command += f" --label {request.label}"
    if request.case_id:
        command += f" --id {request.case_id}"
        
    # 使用线程避免阻塞 API 响应
    thread = threading.Thread(target=run_tests_in_background, args=(command,))
    thread.start()
    
    return {"message": "Test execution started successfully.", "command": command}