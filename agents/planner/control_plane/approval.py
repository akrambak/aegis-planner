# agents/planner/control_plane/approval.py

import os
import requests
import uuid
from agents.planner import memory

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def request_approval(*, task: str, risk_level: str, reason: str) -> bool:
    """
    Sends approval request to Slack and blocks until resolved.
    """

    approval_id = str(uuid.uuid4())

    memory.create_approval_request(
        approval_id=approval_id,
        task=task,
        risk_level=risk_level,
        reason=reason
    )

    payload = {
        "text": "🚨 *AI Task Approval Required*",
        "attachments": [
            {
                "color": "#ffae42",
                "fields": [
                    {"title": "Task", "value": task, "short": False},
                    {"title": "Risk Level", "value": risk_level, "short": True},
                    {"title": "Reason", "value": reason, "short": False}
                ],
                "actions": [
                    {
                        "type": "button",
                        "text": "✅ Approve",
                        "style": "primary",
                        "value": "approve",
                        "action_id": approval_id
                    },
                    {
                        "type": "button",
                        "text": "❌ Deny",
                        "style": "danger",
                        "value": "deny",
                        "action_id": approval_id
                    }
                ]
            }
        ]
    }

    requests.post(SLACK_WEBHOOK_URL, json=payload)

    # ---- BLOCK UNTIL DECISION ----
    return memory.wait_for_approval(approval_id)
