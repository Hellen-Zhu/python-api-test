# core/result_writer.py

import datetime
import os
from sqlalchemy import func, case
from models.tables import AutoProgress, AutoCaseAudit, AutoTestAudit

def create_run_progress(session, run_id, env_info):
    """
    在测试开始时，创建一条初始的总览记录。
    :param session: SQLAlchemy session object.
    :param run_id: The unique ID for this test run.
    :param env_info: A dict containing env, component, tags.
    """
    progress_record = AutoProgress(
        runid=run_id,
        task_status='RUNNING',
        begin_time=datetime.datetime.now(),
        profile=env_info.get("env"),
        label=env_info.get("tags"),
        component=env_info.get("component"),
        run_by=os.getenv('USER', os.getenv('USERNAME', 'unknown')),
        update_time=datetime.datetime.now()
    )
    try:
        session.add(progress_record)
        session.commit()
    except Exception as e:
        print(f"\nERROR: Failed to create initial progress record: {e}")
        session.rollback()

def write_case_audit(session, run_id, case_id, data_set_id, jira_id, display_name, variables, report):
    """
    为单个测试场景写入结果到 auto_case_audit 表。
    :param session: SQLAlchemy session object.
    :param report: Pytest TestReport object.
    :return: The ID of the newly created audit record, or None on failure.
    """
    error_message = report.longreprtext if report.failed else None

    audit_record = AutoCaseAudit(
        runid=run_id,
        case_id=case_id,
        data_set_id=data_set_id,
        issue_key=jira_id,
        scenario=display_name,
        variables=variables,
        run_status=report.outcome, # 'passed', 'failed', 'skipped'
        duration=report.duration,
        error_message=error_message
    )
    try:
        session.add(audit_record)
        session.commit()
        return audit_record.id # 返回新创建记录的ID
    except Exception as e:
        print(f"\nERROR: Failed to write case audit result: {e}")
        session.rollback()
        return None

def write_debug_log(session, audit_case_id, audit_trail):
    """
    将详细的步骤审计日志写入 auto_test_audit 表。
    :param session: SQLAlchemy session object.
    :param audit_case_id: The primary key of the parent auto_case_audit record.
    :param audit_trail: A list of step dictionaries from ApiClient.
    """
    if not audit_case_id: return

    try:
        records_to_add = []
        for step_log in audit_trail:
            records_to_add.append(AutoTestAudit(
                audit_case_id=audit_case_id,
                step_order=step_log.get("step_order"),
                action_description=step_log.get("action_description"),
                request_details=step_log.get("request_details"),
                response_details=step_log.get("response_details"),
                step_status=step_log.get("step_status")
            ))
        if records_to_add:
            session.bulk_save_objects(records_to_add)
            session.commit()
    except Exception as e:
        print(f"\nERROR: Failed to write debug audit log: {e}")
        session.rollback()

def update_run_summary(session, run_id, end_time, status):
    """
    从 auto_case_audit 表中汇总数据，并更新 auto_progress 表。
    :param session: SQLAlchemy session object.
    :param run_id: The unique ID for this test run.
    :param end_time: The timestamp when the session finished.
    :param status: The final status ('PASSED' or 'FAILED').
    """
    try:
        # 1. 从精细结果表中进行聚合查询
        stats = session.query(
            func.count(AutoCaseAudit.id).label("total"),
            func.sum(case((AutoCaseAudit.run_status == 'passed', 1), else_=0)).label("passed"),
            func.sum(case((AutoCaseAudit.run_status == 'failed', 1), else_=0)).label("failed"),
            func.sum(case((AutoCaseAudit.run_status == 'skipped', 1), else_=0)).label("skipped")
        ).filter(AutoCaseAudit.runid == run_id).one()

        # 2. 找到总览记录并更新
        progress_record = session.query(AutoProgress).filter_by(runid=run_id).first()
        if progress_record:
            progress_record.total_cases = stats.total
            progress_record.passes = stats.passed or 0
            progress_record.failures = stats.failed or 0
            progress_record.skips = stats.skipped or 0
            progress_record.end_time = end_time
            progress_record.task_status = status
            progress_record.update_time = datetime.datetime.now()
            session.commit()
            print(f"\n--- Test run summary successfully updated in database (runid: {run_id}) ---")
        else:
            print(f"\nWARNING: Could not find progress record with runid '{run_id}' to update summary.")
    except Exception as e:
        print(f"\nERROR: Failed to update run summary: {e}")
        session.rollback()
