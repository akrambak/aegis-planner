import sqlite3
import json
import time
import os
from datetime import datetime

DB_PATH = "memory/sql/aegis.db"

# -------------------------
# Database helpers
# -------------------------

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------
# Schema Initialization
# -------------------------

def init_schema():
    conn = _connect()
    cur = conn.cursor()

    # Decisions made by planner
    cur.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context TEXT,
            decision TEXT,
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Task history per project
    cur.execute("""
        CREATE TABLE IF NOT EXISTS planner_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project TEXT,
            task TEXT,
            run_date DATE
        );
    """)

    # Daily CEO routines
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            routine_json TEXT,
            run_date DATE
        );
    """)

    # Executions via control plane
    cur.execute("""
        CREATE TABLE IF NOT EXISTS executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT,
            status TEXT,
            result TEXT,
            error TEXT,
            requested_by TEXT,
            dry_run INTEGER,
            executed_at DATETIME
        );
    """)

    conn.commit()
    conn.close()

# -------------------------
# Decision Logging
# -------------------------

def log_decision(context, decision, reason):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO decisions (context, decision, reason) VALUES (?, ?, ?)",
        (context, decision, reason)
    )
    conn.commit()
    conn.close()


# -------------------------
# Task History Logging
# -------------------------

def log_tasks(project, tasks, run_date=None):
    run_date = run_date or datetime.utcnow().date()
    conn = _connect()
    cur = conn.cursor()
    for task in tasks:
        if not isinstance(task, str):
            try:
                task = json.dumps(task, default=str)
            except TypeError:
                task = str(task)
        cur.execute(
            "INSERT INTO planner_tasks (project, task, run_date) VALUES (?, ?, ?)",
            (project, task, run_date)
        )
    conn.commit()
    conn.close()


def get_recent_task_history(days=14):
    """
    Returns task history for last N days
    [(project, task, run_date)]
    """
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT project, task, run_date
        FROM planner_tasks
        WHERE run_date >= date('now', ?)
        """,
        (f"-{days} day",)
    )
    rows = cur.fetchall()
    conn.close()
    return [(r["project"], r["task"], r["run_date"]) for r in rows]


# -------------------------
# Daily Routine Logging
# -------------------------

def save_daily_routine(routine_json, run_date=None):
    run_date = run_date or datetime.utcnow().date()
    if not isinstance(routine_json, str):
        routine_json = json.dumps(routine_json)
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO daily_routines (routine_json, run_date) VALUES (?, ?)",
        (routine_json, run_date)
    )
    conn.commit()
    conn.close()


def get_recent_routines(days=7):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT routine_json, run_date
        FROM daily_routines
        WHERE run_date >= date('now', ?)
        """,
        (f"-{days} day",)
    )
    rows = cur.fetchall()
    conn.close()
    return [(r["routine_json"], r["run_date"]) for r in rows]


# -------------------------
# Execution Logging (Control Plane)
# -------------------------

def _serialize_param(value):
    """Convert non-string values to JSON for SQLite storage."""
    if value is None or isinstance(value, str):
        return value
    try:
        return json.dumps(value, default=str)
    except TypeError:
        return str(value)


def log_execution(
    task,
    status,
    result=None,
    error=None,
    requested_by="system",
    dry_run=True,
    executed_at=None
):
    executed_at = executed_at or datetime.utcnow().isoformat()
    # #region agent log
    try:
        log_path = "/home/ubuntu/aegis-planner/.cursor/debug.log"
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "sessionId": "debug-session",
                "runId": os.getenv("AEGIS_RUN_ID", "unknown"),
                "hypothesisId": "H3",
                "location": "agents/planner/memory.py:log_execution",
                "message": "Logging execution",
                "data": {"task": str(task)[:100], "status": status},
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except OSError:
        pass
    # #endregion
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO executions
        (task, status, result, error, requested_by, dry_run, executed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _serialize_param(task),
            _serialize_param(status),
            _serialize_param(result),
            _serialize_param(error),
            requested_by,
            int(dry_run),
            executed_at
        )
    )
    conn.commit()
    conn.close()


def get_recent_executions(days=7):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM executions
        WHERE executed_at >= datetime('now', ?)
        """,
        (f"-{days} day",)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_policies():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT name, risk_level, task_prefix, action
        FROM policies
        WHERE enabled = 1
        ORDER BY id ASC
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "name": r[0],
            "risk_level": r[1],
            "task_prefix": r[2],
            "action": r[3]
        }
        for r in rows
    ]

def create_approval_request(*, approval_id, task, risk_level, reason):
    """
    Persist a pending approval request in memory storage.
    """

    record = {
        "approval_id": approval_id,
        "task": task,
        "risk_level": risk_level,
        "reason": reason,
        "status": "PENDING"
    }

    if not hasattr(create_approval_request, "_store"):
        create_approval_request._store = {}

    create_approval_request._store[approval_id] = record
    return record



def resolve_approval(*, task_id, approved, approved_by):
    status = "approved" if approved else "denied"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE approvals
        SET status = ?, approved_by = ?, decided_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'pending'
    """, (status, approved_by, task_id))

    updated = cur.rowcount > 0
    conn.commit()
    conn.close()

    return updated


def wait_for_approval(approval_id, timeout=3600):
    import time
    start = time.time()

    while time.time() - start < timeout:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT status FROM approvals WHERE id = ?", (approval_id,))
        row = cur.fetchone()
        conn.close()

        if row and row[0] in ("approved", "denied"):
            return row[0] == "approved"

        time.sleep(2)

    return False

def mark_execution_blocked(*, task: str, approval_id: str, requested_by: str):
    """
    Records a blocked execution awaiting approval.
    """

    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO executions
        (task, status, result, error, requested_by, dry_run, executed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _serialize_param(task),
            "blocked",
            f"Awaiting approval {approval_id}",
            None,
            requested_by,
            1,
            datetime.utcnow().isoformat()
        )
    )

    conn.commit()
    conn.close()


# -------------------------
# Initialize schema automatically on import
# -------------------------
init_schema()

