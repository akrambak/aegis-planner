import subprocess
import json
import time
import os
from datetime import datetime
from agents.planner import memory

# ------------------------------
# Core execution function
# ------------------------------
def execute_task(task):
    """
    task: dict with keys:
      - task_type: shell | python | git | deploy | api
      - payload: string or JSON
    """
    if not isinstance(task, dict):
        return "failed", None, "Invalid task format; expected dict"

    task_type = task.get("task_type")
    payload = task.get("payload")
    # #region agent log
    try:
        log_path = "/home/ubuntu/aegis-planner/.cursor/debug.log"
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "sessionId": "debug-session",
                "runId": os.getenv("AEGIS_RUN_ID", "unknown"),
                "hypothesisId": "H2",
                "location": "agents/planner/executor.py:execute_task",
                "message": "Executor received dict task",
                "data": {
                    "task_type": task_type,
                    "payload_preview": str(payload)[:80]
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except OSError:
        pass
    # #endregion
    result = ""
    status = "success"
    error = None
    start_time = datetime.utcnow()

    try:
        if task_type == "shell":
            result = subprocess.run(
                payload, shell=True, capture_output=True, text=True, check=True
            ).stdout

        elif task_type == "python":
            # Execute python code safely
            local_vars = {}
            exec(payload, {}, local_vars)
            result = str(local_vars)

        elif task_type == "git":
            # Example: payload = "git pull origin main"
            result = subprocess.run(
                payload, shell=True, capture_output=True, text=True, check=True
            ).stdout

        elif task_type == "deploy":
            # Example placeholder
            result = f"Deploy executed: {payload}"

        elif task_type == "api":
            # Example: JSON with url, method, data
            data = json.loads(payload)
            import requests
            resp = requests.request(data.get("method", "GET"), data["url"], json=data.get("json"))
            result = resp.text

        else:
            status = "failed"
            error = f"Unknown task_type: {task_type}"

    except Exception as e:
        status = "failed"
        error = str(e)

    run_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    # Log execution in memory
    memory.log_execution(
        task_type=task_type,
        payload=payload,
        status=status,
        result=result,
        error=error,
        run_time_ms=run_time
    )

    return status, result, error
