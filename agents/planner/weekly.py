import sqlite3
import json
from datetime import datetime, timedelta
from agents.planner.llm import get_planner_llm, run_planner_prompt
from agents.planner import memory

DB_PATH = "memory/sql/aegis.db"

# -----------------------------
# Helper: get last 30 days of task history
# -----------------------------
def get_recent_history(days=30):
    conn = sqlite3.connect(DB_PATH)
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

    return [
        {"project": r[0], "task": r[1], "run_date": r[2]}
        for r in rows
    ]


# -----------------------------
# Weekly analysis
# -----------------------------
def analyze_projects():
    history = get_recent_history()
    score = {}

    for h in history:
        project = h["project"]
        score[project] = score.get(project, 0) + 1

    return [
        {
            "name": project,
            "recent_tasks": count,
            "risk": count < 2
        }
        for project, count in score.items()
    ]


# -----------------------------
# Generate weekly CEO routine via LLM
# -----------------------------
def generate_weekly_routine(projects_analysis):
    llm = get_planner_llm()

    prompt = (
        "You are an elite CEO weekly planner.\n"
        "Given the following projects analysis (recent task counts, failures, risk flags):\n" +
        json.dumps(projects_analysis, indent=2) +
        "\n\nCreate a weekly plan (7 days) with time blocks per day. "
        "Return strict JSON only:\n"
        "{ \"week_start\": \"YYYY-MM-DD\", "
        "\"schedule\": [ {\"day\": \"Monday\", \"tasks\": [\"...\"]} ] }"
    )

    response = run_planner_prompt(llm, prompt)

    try:
        return json.loads(response)
    except Exception:
        # fallback schedule
        today = datetime.utcnow().date()
        return {
            "week_start": str(today),
            "schedule": [
                {"day": "Monday", "tasks": ["Top project work"]},
                {"day": "Tuesday", "tasks": ["Secondary projects"]},
                {"day": "Wednesday", "tasks": ["Deep work"]},
                {"day": "Thursday", "tasks": ["Review & adjust"]},
                {"day": "Friday", "tasks": ["Follow-up & decisions"]},
                {"day": "Saturday", "tasks": ["Planning & minor tasks"]},
                {"day": "Sunday", "tasks": ["Strategic review"]},
            ]
        }

# -----------------------------
# Save weekly strategy to SQLite
# -----------------------------
def save_weekly_strategy(strategy_dict):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO weekly_strategy (week_start, strategy_json) VALUES (?, ?)",
        (strategy_dict["week_start"], json.dumps(strategy_dict))
    )
    conn.commit()
    conn.close()

# -----------------------------
# Full weekly planner pipeline
# -----------------------------
def run_weekly_planner():
    print("\n📊 ===== WEEKLY STRATEGIC PLANNER =====")
    projects_analysis = analyze_projects()
    strategy = generate_weekly_routine(projects_analysis)
    save_weekly_strategy(strategy)

    print(f"\n📅 Week Start: {strategy['week_start']}")
    for day in strategy["schedule"]:
        print(f"{day['day']}:")
        for task in day["tasks"]:
            print(f"  - {task}")

    print("==============================\n")
    return strategy
