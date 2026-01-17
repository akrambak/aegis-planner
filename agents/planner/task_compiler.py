# agents/planner/task_compiler.py
from typing import List, Dict

SAFE_SHELL_PREFIXES = ["python ", "pip ", "git ", "docker ", "bash ", "sh "]

def compile_task(raw_task: str) -> Dict:
    """
    Convert raw text to a structured task object.
    """
    task_lower = raw_task.lower()
    if any(task_lower.startswith(p) for p in SAFE_SHELL_PREFIXES):
        return {"type": "shell", "payload": raw_task}
    elif task_lower.startswith("n8n "):
        return {"type": "n8n", "payload": raw_task[4:].strip()}
    elif task_lower.startswith("api "):
        return {"type": "api", "payload": raw_task[4:].strip()}
    else:
        return {"type": "human", "payload": raw_task}

def compile_tasks(raw_tasks: List[str]) -> List[Dict]:
    return [compile_task(t) for t in raw_tasks]
