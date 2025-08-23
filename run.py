# run.py

import pytest
import argparse
import os
import sys
from dotenv import load_dotenv

# 全局配置加载
print("--- Loading framework database configuration from .env file ---")
load_dotenv()

DEFAULT_ENV = 'dev'

def main():
    """
    框架主执行入口。
    负责解析命令行参数，确定运行环境，然后启动 pytest。
    """
    env_from_os = os.getenv('TEST_ENV')
    parallel_from_os = os.getenv('PYTEST_PARALLEL_WORKERS')

    parser = argparse.ArgumentParser(
        description="API Test Runner - A highly configurable, data-driven framework.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # --- 环境参数 ---
    parser.add_argument(
        "--env",
        type=str,
        default=parallel_from_os, # 使用环境变量作为默认值
        help=f"指定测试目标环境 (e.g., dev, uat)。\n"
             f"优先级: 命令行 > 环境变量 TEST_ENV > 默认值 '{DEFAULT_ENV}'。"
    )

    # --- 并行执行参数 ---
    parser.add_argument(
        "-n", "--parallel",
        type=str,
        default=None,
        help="并行执行的进程数 (e.g., 4, 8, or 'auto' to use all available CPU cores)."
    )

    # --- 其他所有筛选和功能参数 ---
    parser.add_argument("--service", type=str, help="按服务筛选")
    parser.add_argument("--module", type=str, help="按模块筛选")
    parser.add_argument("--component", type=str, help="按组件筛选")
    parser.add_argument("--tags", type=str, help="按标签筛选，多个用逗号隔开 (e.g., P0,smoke)")
    parser.add_argument("--jira", type=str, help="按Jira ID筛选")
    parser.add_argument("--id", type=int, help="按用例模板ID(case_id)执行其所有数据集")
    parser.add_argument("--debug-mode", action="store_true", help="开启Debug模式，会将详细审计日志写入数据库")

    args = parser.parse_args()

    # 确定最终使用的环境
    final_env = args.env or env_from_os or DEFAULT_ENV

    print(f"\n--- Final environment for this run: {final_env} ---")
    print(f"--- (Source: {'Command-line' if args.env else ('Environment Variable' if env_from_os else 'Hardcoded Default')}) ---")
    print(f"--- (Source: {'Command-line' if args.env else ('Environment Variable' if parallel_from_os else 'Hardcoded Default')}) ---")

    # 准备 pytest 的参数列表
    report_dir = 'reports/allure-results'
    pytest_args = ['tests/test_main.py', '-v', '--alluredir', report_dir]

    # 将所有解析到的参数正确地传递给 pytest
    pytest_args.append(f"--env={final_env}")
    if args.parallel:
        pytest_args.extend(["-n", args.parallel])
    if args.service: pytest_args.append(f"--service={args.service}")
    if args.module: pytest_args.append(f"--module={args.module}")
    if args.component: pytest_args.append(f"--component={args.component}")
    if args.tags: pytest_args.append(f"--tags={args.tags}")
    if args.jira: pytest_args.append(f"--jira={args.jira}")
    if args.id: pytest_args.append(f"--id={args.id}")
    if args.debug_mode: pytest_args.append("--debug-mode")

    # 运行 pytest 并生成报告
    if os.path.exists(report_dir):
        import shutil
        shutil.rmtree(report_dir)

    pytest.main(pytest_args)
    try:
        print("正在启动 Allure 报告服务...")
        # allure serve 会自动打开浏览器并显示报告
        os.system(f'allure serve {report_dir}')
    except Exception as e:
        print(f"启动 Allure 服务失败: {e}")
        # 备用方案：生成静态报告
        os.system(f'allure generate {report_dir} -o reports/allure-report --clean')
    #
    # exit_code = pytest.main(pytest_args)
    #
    # print("\n测试执行完成. 正在生成 Allure 报告...")
    # os.system(f'allure generate {report_dir} -o reports/allure-report --clean')
    #
    # sys.exit(exit_code)

if __name__ == '__main__':
    main()
