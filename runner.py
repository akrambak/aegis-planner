"""
PHASE 15 — CEO PLANNER CONTROL LOOP
----------------------------------
This runner is the ONLY entrypoint for autonomous planning.
Execution is routed through the Control Plane + API boundary.
"""

from datetime import datetime
import socket
import uuid
import json
import time

from agents.planner.graph import planner_app, PlannerState, Project
from agents.planner.intelligence import (
    adjust_project_priorities,
    generate_ceo_daily_routine
)
from agents.planner.weekly import run_weekly_planner
from control_plane.api import execute_task_api
from agents.planner import memory


# ================================
# CONFIG
# ================================

DRY_RUN = False          # Set True for safe testing
RUN_WEEKLY_ON_MONDAY = True

NODE_ID = socket.gethostname()
RUN_ID = str(uuid.uuid4())

# #region agent log
def _debug_log(payload: dict) -> None:
    try:
        log_path = "/home/ubuntu/aegis-planner/.cursor/debug.log"
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
    except OSError:
        pass
# #endregion


# ================================
# PROJECT LOADER
# ================================

def load_projects():
    """
    Static loader for now.
    Replace with DB / API loader later.
    """
    return [
        Project("Project Alpha", priority=3),
        Project("Project Beta", priority=2),
        Project("Project Gamma", priority=1),
    ]


# ================================
# MAIN DAILY LOOP
# ================================

def run_daily_planner():
    # #region agent log
    _debug_log({
        "sessionId": "debug-session",
        "runId": RUN_ID,
        "hypothesisId": "H1",
        "location": "runner.py:run_daily_planner:entry",
        "message": "Starting planner run",
        "data": {"node_id": NODE_ID, "dry_run": DRY_RUN},
        "timestamp": int(time.time() * 1000)
    })
    # #endregion
    print("\n🧠 ===== CEO PLANNER RUN =====")
    print(f"Run ID: {RUN_ID}")
    print(f"Node  : {NODE_ID}")
    print(f"Mode  : {'DRY RUN' if DRY_RUN else 'LIVE'}")

    started_at = datetime.utcnow().isoformat()

    # ---- LOAD + PRIORITIZE PROJECTS ----
    projects = load_projects()
    projects = adjust_project_priorities(projects)

    # ---- PLANNER GRAPH ----
    state = PlannerState(projects=projects)
    updated_state = planner_app.run(state)

    top_focus = updated_state.top_focus
    tasks = updated_state.constraints.get("tasks", [])

    # ---- MEMORY: DECISION LOG ----
    memory.log_decision(
        context="daily_planning",
        decision=top_focus,
        reason="LLM-based prioritization"
    )

    project_name = top_focus.split("—")[0].strip()
    memory.log_tasks(project_name, tasks)

    # ---- CEO DAILY ROUTINE ----
    routine = generate_ceo_daily_routine(projects)
    memory.save_daily_routine(routine)

    # ---- EXECUTION VIA CONTROL PLANE ----
    print("\n🚀 EXECUTING TASKS (CONTROL PLANE):")

    for idx, task in enumerate(tasks, 1):
        # #region agent log
        _debug_log({
            "sessionId": "debug-session",
            "runId": RUN_ID,
            "hypothesisId": "H1",
            "location": "runner.py:run_daily_planner:task_loop",
            "message": "Dispatching task",
            "data": {
                "task_type": type(task).__name__,
                "task_preview": str(task)[:80]
            },
            "timestamp": int(time.time() * 1000)
        })
        # #endregion
        record = execute_task_api(
            task=task,
            requested_by="planner",
            dry_run=DRY_RUN
        )

        status = record["status"]
        error = record.get("error")

        print(f"{idx}. [{status.upper()}] {task}")
        if error:
            print(f"   ⚠ {error}")

    # ---- SUMMARY OUTPUT ----
    print("\n🎯 TOP FOCUS:")
    print(top_focus)

    print("\n🕒 DAILY ROUTINE:")
    for block in routine["schedule"]:
        print(f"{block['time']} → {block['task']}")

    finished_at = datetime.utcnow().isoformat()

    # ---- TELEMETRY SNAPSHOT ----
    memory.log_execution(
        task="DAILY_PLANNER_RUN",
        status="success",
        result=f"{len(tasks)} tasks processed",
        error=None,
        requested_by="system",
        dry_run=DRY_RUN,
        executed_at=finished_at
    )

    print("\n==============================")
    print("Planner run completed.")
    print("==============================\n")


def autonomy_enabled():
    value = memory.get_flag("AUTONOMY_ENABLED")
    return value != "false"


# ================================
# ENTRYPOINT
# ================================

if __name__ == "__main__":
    run_daily_planner()

    # ---- WEEKLY STRATEGIC PLANNER ----
    if RUN_WEEKLY_ON_MONDAY and datetime.utcnow().weekday() == 0:
        print("\n📊 ===== WEEKLY STRATEGIC PLANNER =====")
        run_weekly_planner()

