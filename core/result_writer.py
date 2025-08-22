# core/result_writer.py

import datetime
from core import db_handler
from models.tables import AutoProgress, AutoTestAudit

def write_run_summary(summary_data: dict):
    """
    将一次测试运行的概要信息写入到 auto_progress 表中。
    """
    if not db_handler.Session:
        print("\nWARNING: Database session not initialized. Skipping summary writing.")
        return

    progress_record = AutoProgress(
        runid=summary_data.get("run_id"),
        component=summary_data.get("component"),
        total_cases=summary_data.get("total"),
        passes=summary_data.get("passed"),
        failures=summary_data.get("failed"),
        skips=summary_data.get("skipped"),
        begin_time=summary_data.get("start_time"),
        end_time=summary_data.get("end_time"),
        task_status=summary_data.get("status"),
        run_by=summary_data.get("run_by"),
        label=summary_data.get("tags"),
        runmode='pytest',
        profile=summary_data.get("env"),
        update_time=datetime.datetime.now()
    )

    try:
        with db_handler.Session() as session:
            session.add(progress_record)
            session.commit()
        print(f"\n--- Test run summary successfully written to database (runid: {summary_data.get('run_id')}) ---")
    except Exception as e:
        print(f"\nERROR: Failed to write test run summary to database: {e}")


def write_audit_log(run_id: str, case_id: int, data_set_id: int, audit_trail: list):
    """
    将一个测试场景的详细审计日志写入 auto_test_audit 表。
    """
    if not db_handler.Session:
        print("\nWARNING: DB session not initialized. Skipping audit log writing.")
        return

    try:
        with db_handler.Session() as session:
            records_to_add = []
            # 遍历审计轨迹,为每一步创建一个ORM对象
            for step_log in audit_trail:
                audit_record = AutoTestAudit(
                    runid=run_id, # 使用全局的 RUN_ID
                    case_id=case_id,
                    data_set_id=data_set_id,
                    step_order=step_log.get("step_order"),
                    action_description=step_log.get("action_description"),
                    request_details=step_log.get("request_details"),
                    response_details=step_log.get("response_details"),
                    step_status=step_log.get("step_status")
                )
                records_to_add.append(audit_record)

            # 使用 session.bulk_save_objects() 批量插入,性能更佳
            if records_to_add:
                session.bulk_save_objects(records_to_add)
                session.commit()
                print(f"\n--- [DEBUG MODE] Detailed audit log for case_id={case_id} successfully written to database. ---")

    except Exception as e:
        print(f"\nERROR: Failed to write audit log to database: {e}")
