"""
Risk classification for planner control plane.
"""

from typing import Dict, List, Any
import json


RISK_MATRIX: Dict[str, List[str]] = {
    "LOW": [
        "git ",
        "pip ",
        "python ",
        "pytest ",
        "echo ",
    ],
    "MEDIUM": [
        "docker ",
        "bash ",
        "sh ",
        "make ",
    ],
    "HIGH": [
        "rm ",
        "sudo ",
        "shutdown",
        "reboot",
        "mkfs",
        "dd ",
        ":(){",  # fork bomb
    ],
}


def _task_to_text(task: Any) -> str:
    if task is None:
        return ""
    if isinstance(task, str):
        return task
    if isinstance(task, dict):
        for key in ("command", "task", "payload", "description", "name"):
            value = task.get(key)
            if isinstance(value, str):
                return value
        if "payload" in task:
            try:
                return json.dumps(task["payload"], default=str)
            except TypeError:
                return str(task["payload"])
        try:
            return json.dumps(task, default=str)
        except TypeError:
            return str(task)
    try:
        return json.dumps(task, default=str)
    except TypeError:
        return str(task)


def assess_risk(task: Any) -> str:
    """
    Determine the risk level of a task.
    Returns: LOW | MEDIUM | HIGH
    """
    task_text = _task_to_text(task)
    if not task_text:
        return "MEDIUM"

    task_lower = task_text.strip().lower()

    for level, prefixes in RISK_MATRIX.items():
        for prefix in prefixes:
            if task_lower.startswith(prefix):
                return level

    return "MEDIUM"
