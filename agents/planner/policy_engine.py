# agents/planner/policy_engine.py

from agents.planner import memory

def evaluate_policy(task: str, risk_level: str):
    """
    Returns: approve | deny | require_approval
    """

    policies = memory.get_active_policies()

    task_lower = task.lower()

    for p in policies:
        if p["risk_level"] and p["risk_level"] != risk_level:
            continue

        if p["task_prefix"]:
            if not task_lower.startswith(p["task_prefix"].lower()):
                continue

        return p["action"], p["name"]

    # Default fallback (SAFE BY DESIGN)
    return "require_approval", "Default fallback policy"
