"""
Control Plane Execution API
---------------------------
This module is the ONLY allowed execution entrypoint.
It enforces:
- Risk classification
- Human approval (via n8n)
- Full audit logging
"""

from datetime import datetime
from typing import Dict, Any
import os
import json
import time
import socket
import requests

from control_plane.risk import assess_task_risk
from agents.planner.control_plane import control_execute
from agents.planner import memory


# ================================
# CONFIG
# ================================

N8N_APPROVAL_WEBHOOK = os.getenv(
    "N8N_APPROVAL_WEBHOOK",
    "http://localhost:5678/webhook/task-approval"
)

SLACK_FAILURE_WEBHOOK = os.getenv("SLACK_FAILURE_WEBHOOK") or os.getenv("SLACK_WEBHOOK_URL")
NODE_NAME = os.getenv("NODE_NAME") or socket.gethostname()

N8N_TIMEOUT_SECONDS = 15


# ================================
# EXECUTION API
# ================================

def execute_task_api(
    task: str,
    requested_by: str = "system",
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    External-safe execution API.
    Returns a structured execution record.
    """

    executed_at = datetime.utcnow().isoformat()
    # #region agent log
    try:
        log_path = "/home/ubuntu/aegis-planner/.cursor/debug.log"
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "sessionId": "debug-session",
                "runId": os.getenv("AEGIS_RUN_ID", "unknown"),
                "hypothesisId": "H1",
                "location": "control_plane/api.py:execute_task_api",
                "message": "Preparing control_execute call",
                "data": {"task_type": type(task).__name__, "dry_run": dry_run},
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except OSError:
        pass
    # #endregion
    risk_level = assess_task_risk(task)

    approved = True
    approval_source = "auto"

    # ----------------
    # HUMAN APPROVAL GATE
    # ----------------
    if risk_level == "high":
        approval_source = "n8n"
        approved = False

        payload = {
            "task": task,
            "risk_level": risk_level,
            "requested_by": requested_by,
            "dry_run": dry_run,
            "timestamp": executed_at,
        }

        try:
            response = requests.post(
                N8N_APPROVAL_WEBHOOK,
                json=payload,
                timeout=N8N_TIMEOUT_SECONDS
            )

            if response.status_code == 200:
                data = response.json()
                approved = bool(data.get("approved", False))
            else:
                approved = False

        except Exception as exc:
            approved = False
            error = f"Approval webhook failed: {exc}"

    # ----------------
    # EXECUTION
    # ----------------
    if not approved:
        status = "skipped"
        result = None
        error = "Task rejected or not approved"

    else:
        try:
            status, result, error = control_execute(
                task=task,
                requested_by=requested_by,
                dry_run=dry_run
            )
        except Exception as exc:
            status = "failed"
            result = None
            error = str(exc)

    # ----------------
    # AUDIT LOG
    # ----------------
    record = {
        "task": task,
        "status": status,
        "result": result,
        "error": error,
        "requested_by": requested_by,
        "dry_run": dry_run,
        "executed_at": executed_at,
        "risk_level": risk_level,
        "approved": approved,
        "approval_source": approval_source,
    }

    memory.log_execution(
        task=task,
        status=status,
        result=result,
        error=error,
        requested_by=requested_by,
        dry_run=dry_run,
        executed_at=executed_at,
    )

    if status == "failed":
        _notify_slack_failure(
            task=task,
            error=error,
            run_id=os.getenv("AEGIS_RUN_ID", "unknown"),
            node=NODE_NAME,
            executed_at=executed_at,
        )

    return record


def _notify_slack_failure(task: str, error: str | None, run_id: str, node: str, executed_at: str):
    if not SLACK_FAILURE_WEBHOOK:
        return

    payload = {
        "text": "⚠️ Task Failure Alert",
        "attachments": [
            {
                "color": "#ff4d4f",
                "fields": [
                    {"title": "Task", "value": task, "short": False},
                    {"title": "Error", "value": error or "Unknown error", "short": False},
                    {"title": "Run ID", "value": run_id, "short": True},
                    {"title": "Node", "value": node, "short": True},
                    {"title": "Executed At", "value": executed_at, "short": False},
                ],
            }
        ],
    }

    try:
        requests.post(SLACK_FAILURE_WEBHOOK, json=payload, timeout=5)
    except requests.RequestException:
        pass

