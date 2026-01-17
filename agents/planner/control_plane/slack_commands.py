import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from agents.planner.memory import create_approval_request


class SlackCommandHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")

        payload = self.parse_body(raw_body)
        command = payload.get("command")

        if command == "/approve":
            response = approve(payload)
        elif command == "/deny":
            response = deny(payload)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Unknown command")
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))

    @staticmethod
    def parse_body(body: str) -> dict:
        parts = body.split("&")
        data = {}
        for part in parts:
            if "=" in part:
                k, v = part.split("=", 1)
                data[k] = v
        return data


def approve(payload: dict):
    approval_id = payload.get("text")

    return {
        "status": "APPROVED",
        "approval_id": approval_id
    }


def deny(payload: dict):
    approval_id = payload.get("text")

    return {
        "status": "DENIED",
        "approval_id": approval_id
    }


def run_slack_command_server(host: str = "0.0.0.0", port: int = 3333):
    """
    Local HTTP server to receive Slack slash commands.
    """

    server = HTTPServer((host, port), SlackCommandHandler)
    print(f"[CONTROL PLANE] Slack command server running on {host}:{port}")
    server.serve_forever()

