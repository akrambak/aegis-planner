-- Projects tracked by the planner
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  vision TEXT,
  status TEXT,
  priority INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tasks generated or approved by planner
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER,
  description TEXT NOT NULL,
  status TEXT,
  outcome TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Daily execution logs
CREATE TABLE IF NOT EXISTS daily_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT UNIQUE,
  focus TEXT,
  wins TEXT,
  failures TEXT,
  agent_verdict TEXT
);

-- Planner decisions (important)
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  context TEXT,
  decision TEXT,
  reason TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-------------------------------------
-------------------------------------

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-------------------------------------------------
-- SYSTEM METADATA
-------------------------------------------------
CREATE TABLE IF NOT EXISTS system_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-------------------------------------------------
-- PLANNER DECISIONS (LONG-TERM MEMORY)
-------------------------------------------------
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    context TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    confidence REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_decisions_context
ON decisions(context);

-------------------------------------------------
-- PLANNER TASK HISTORY
-------------------------------------------------
CREATE TABLE IF NOT EXISTS planner_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    task TEXT NOT NULL,
    priority INTEGER DEFAULT 3,
    status TEXT DEFAULT 'pending',  -- pending | running | done | failed
    run_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_planner_tasks_project
ON planner_tasks(project);

-------------------------------------------------
-- DAILY CEO ROUTINES
-------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_routines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    routine_json TEXT NOT NULL,
    run_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-------------------------------------------------
-- AGENT REGISTRY
-------------------------------------------------
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    model TEXT,
    temperature REAL DEFAULT 0.2,
    tools TEXT, -- JSON list of allowed tools
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-------------------------------------------------
-- AGENT EXECUTION LOGS
-------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    input TEXT,
    output TEXT,
    status TEXT DEFAULT 'success', -- success | error
    error TEXT,
    run_time_ms INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_name) REFERENCES agents(name)
);

-------------------------------------------------
-- EXECUTION TASKS (REAL ACTIONS)
-------------------------------------------------
CREATE TABLE IF NOT EXISTS execution_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL, -- shell | python | git | deploy | api
    payload TEXT NOT NULL,   -- JSON instructions
    status TEXT DEFAULT 'queued', -- queued | running | done | failed
    result TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-------------------------------------------------
-- SCHEDULER JOBS
-------------------------------------------------
CREATE TABLE IF NOT EXISTS scheduler_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT UNIQUE NOT NULL,
    job_type TEXT NOT NULL, -- planner | ceo | executor
    cron TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    last_run DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-------------------------------------------------
-- ERROR LOGGING
-------------------------------------------------
CREATE TABLE IF NOT EXISTS system_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    message TEXT,
    traceback TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-------------------------------------------------
-- BOOTSTRAP DATA
-------------------------------------------------
INSERT OR IGNORE INTO system_meta (key, value)
VALUES ('schema_version', '1.0');

