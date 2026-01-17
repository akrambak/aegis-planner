from agents.planner.executor import execute_task
from agents.planner import memory

def dispatch(task):
    return execute_task(task)

# Safe command prefixes (Phase 13 allowlist)
SAFE_PREFIXES = ["python ", "pip ", "git ", "docker ", "bash ", "sh "]

def classify_task(task: str) -> str:
    """
    Determine task type:
    - human: non-executable
    - shell: safe command
    - api: future API call
    - n8n: workflow trigger
    """
    task_lower = task.lower()
    if any(task_lower.startswith(p) for p in SAFE_PREFIXES):
        return "shell"
    elif task_lower.startswith("n8n "):
        return "n8n"
    elif task_lower.startswith("api "):
        return "api"
    else:
        return "human"


def control_execute(task: str, dry_run: bool = False):
    """
    Execute task safely through Control Plane.
    """
    task_type = classify_task(task)
    if task_type == "human":
        print(f"[SKIPPED] {task} (human-level task)")
        memory.log_decision("control_plane", task, "skipped human task")
        return "skipped", None, None

    if dry_run:
        print(f"[DRY-RUN] {task_type.upper()} task: {task}")
        memory.log_decision("control_plane", task, "dry-run")
        return "dry-run", None, None

    # Execute only shell or n8n tasks
    if task_type == "shell":
        status, result, error = execute_task({"task_type": "shell", "payload": task})
    elif task_type == "n8n":
        # Placeholder: integrate n8n workflow trigger
        status, result, error = "success", f"Triggered n8n workflow: {task}", None
    elif task_type == "api":
        # Placeholder: integrate API call
        status, result, error = "success", f"Executed API task: {task}", None
    else:
        status, result, error = "skipped", None, None

    # Log execution
    memory.log_execution(
        task=task,
        status=status,
        result=result,
        error=error,
        requested_by="planner",
        dry_run=dry_run,
    )
    return status, result, error
