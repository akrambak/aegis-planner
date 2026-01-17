# agents/planner/control_plane/policy.py

from typing import Dict, Tuple


POLICY_VERSION = "1.0"


def evaluate_policy(
    *,
    task: str,
    risk_level: str,
    requested_by: str = "planner"
) -> Tuple[str, str]:
    """
    Evaluate execution policy for a given task.

    Returns:
        decision: one of ["allow", "require_approval", "deny"]
        reason: human-readable explanation
    """

    risk_level = risk_level.lower().strip()

    # ---- RULE SET v1 ----

    if risk_level == "low":
        return (
            "allow",
            "Low risk task auto-approved by policy"
        )

    if risk_level == "medium":
        return (
            "require_approval",
            "Medium risk task requires human approval"
        )

    if risk_level == "high":
        return (
            "deny",
            "High risk task denied by policy"
        )

    # ---- DEFAULT FAIL SAFE ----
    return (
        "deny",
        f"Unknown risk level '{risk_level}' — denied by default"
    )
