# agents/planner/executor_adapter.py
from agents.planner.control_plane import control_execute

def run_task(task: dict, dry_run: bool = False):
    """
    Executes a structured task safely.
    """
    task_type = task.get("type")
    payload = task.get("payload")

    # human tasks never execute
    if task_type == "human":
        print(f"[SKIPPED] Human task: {payload}")
        return "skipped", None, None

    # delegate to control plane
    return control_execute(payload, dry_run=dry_run)

def run_all(tasks: list, dry_run: bool = False):
    results = []
    for t in tasks:
        status, output, error = run_task(t, dry_run)
        results.append({"task": t, "status": status, "output": output, "error": error})
    return results
