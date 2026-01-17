from agents.planner.llm import get_planner_llm, run_planner_prompt
from collections import Counter
from agents.planner import memory
import json


def adjust_project_priorities(projects):
    """
    Adjust priorities based on recent task history.
    """
    history = memory.get_recent_task_history(days=14)

    # Count tasks per project
    project_counts = Counter(
        h["project"] if isinstance(h, dict) else h[0] for h in history
    )

    for project in projects:
        boost = project_counts.get(project.name, 0)
        project.priority += boost

    # Sort projects by new priority (descending)
    projects.sort(key=lambda p: p.priority, reverse=True)

    return projects


def generate_ceo_daily_routine(projects):
    fallback_routine = {
        "schedule": [
            {"time": "09:00", "task": "Deep work on top project"},
            {"time": "13:00", "task": "Execution & follow-ups"},
            {"time": "16:30", "task": "Review & planning"}
        ]
    }

    try:
        llm = get_planner_llm()
    except RuntimeError:
        return fallback_routine

    prompt = (
        "You are an elite CEO planner.\n"
        "Projects:\n" +
        "\n".join(f"- {p.name} (priority {p.priority})" for p in projects) +
        "\n\nGenerate a strict JSON daily routine:\n"
        "{ \"schedule\": [ {\"time\": \"09:00\", \"task\": \"...\"} ] }"
    )

    try:
        response = run_planner_prompt(llm, prompt)
        return json.loads(response)
    except Exception:
        return fallback_routine

