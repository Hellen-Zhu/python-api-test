# run.py
import sys
import pytest
import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="API Test Runner")
    # ... (argparse 部分不变)
    parser.add_argument("--env", type=str,default="uat", required=True, help="Execution environment (dev, staging)")

    if len(sys.argv) == 1:
        sys.argv.append("--env")
        sys.argv.append("uat")
    
    args = parser.parse_args()

    # 【修正】--alluredir 和它的值是两个独立的字符串
    report_dir = 'reports/allure-results'
    pytest_args = ['tests/test_main.py', '-v', '--alluredir', report_dir]

    # ... (添加 component, label, id 的逻辑不变)

    pytest_args.append(f"--env={args.env}")

    # 在运行前清空旧的报告结果
    if os.path.exists(report_dir):
        import shutil
        shutil.rmtree(report_dir)

    pytest.main(pytest_args)

    print("\n测试执行完成. 生成 Allure 报告...")
    try:
        print("正在启动 Allure 报告服务...")
        # allure serve 会自动打开浏览器并显示报告
        os.system(f'allure serve {report_dir}')
    except Exception as e:
        print(f"启动 Allure 服务失败: {e}")
        # 备用方案：生成静态报告
        os.system(f'allure generate {report_dir} -o reports/allure-report --clean')
        print("已生成静态报告,请手动打开 reports/allure-report/index.html")