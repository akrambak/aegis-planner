from agents.planner.memory import (
    create_approval_request,
    mark_execution_blocked,
)
from agents.planner.control_plane.risk import assess_risk
from agents.planner.executor import execute_task


def control_execute(*, task: str, requested_by: str, dry_run: bool = True):
    """
    Central approval gate for ALL executions.
    """

    risk = assess_risk(task)

    if risk == "HIGH":
        approval_id = create_approval_request(
            task=task,
            risk_level=risk,
            reason="High-risk operation requires approval"
        )

        mark_execution_blocked(
            task=task,
            approval_id=approval_id,
            requested_by=requested_by
        )

        return "BLOCKED", None, f"Awaiting approval {approval_id}"

    # LOW / MEDIUM → auto-execute
    if dry_run:
        return "SKIPPED", None, "Dry run"

    status, result, error = execute_task(task)
    return status, result, error

