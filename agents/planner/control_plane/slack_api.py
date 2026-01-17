# agents/planner/control_plane/slack_api.py

import json
from flask import Flask, request, jsonify
from agents.planner import memory

app = Flask(__name__)


@app.route("/slack/approval", methods=["POST"])
def handle_approval():
    payload = json.loads(request.form["payload"])
    action = payload["actions"][0]["value"]
    task_id = payload["actions"][0]["action_id"]

    approved = action == "approve"

    memory.resolve_approval(
        task_id=task_id,
        approved=approved,
        approved_by=payload["user"]["username"]
    )

    return jsonify({
        "text": f"✅ Task {'approved' if approved else 'denied'}"
    })


def run_slack_server():
    app.run(host="0.0.0.0", port=5055)
