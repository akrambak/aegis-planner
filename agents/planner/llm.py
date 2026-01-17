import os
import json
import time
from typing import Optional

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        return None

load_dotenv()


# #region agent log
def _debug_log(payload: dict) -> None:
    try:
        log_path = "/home/ubuntu/aegis-planner/.cursor/debug.log"
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
    except OSError:
        pass
# #endregion


# Read API key and model from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.json")

if not OPENROUTER_API_KEY:
    # #region agent log
    _debug_log({
        "sessionId": "debug-session",
        "runId": os.getenv("AEGIS_RUN_ID", "unknown"),
        "hypothesisId": "H1",
        "location": "agents/planner/llm.py:env_check",
        "message": "OPENROUTER_API_KEY missing - LLM features disabled",
        "data": {"has_api_key": False, "model": OPENROUTER_MODEL},
        "timestamp": int(time.time() * 1000)
    })
    # #endregion
    # Don't raise - allow graceful degradation with fallback logic


def load_system_prompt(path: str = SYSTEM_PROMPT_PATH) -> str:
    """
    Load the system prompt from a JSON file.
    Returns an empty string if the file is missing or invalid.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        prompt = data.get("system_prompt", "")
        if not isinstance(prompt, str):
            return ""
        return prompt.strip()
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return ""


class PlannerLLM:
    """
    Simple OpenRouter-based LLM client for Planner Agent.
    Uses REST API directly via requests.
    """

    def __init__(self, api_key: str = OPENROUTER_API_KEY, model: str = OPENROUTER_MODEL):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.system_prompt = load_system_prompt()

    def run_prompt(self, prompt: str) -> str:
        """
        Sends a prompt to OpenRouter and returns the response text.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        }

        response = requests.post(self.endpoint, headers=headers, data=json.dumps(payload))

        if response.status_code != 200:
            raise RuntimeError(f"OpenRouter API error {response.status_code}: {response.text}")

        data = response.json()

        # Return the assistant text
        return data["choices"][0]["message"]["content"]


def get_planner_llm() -> PlannerLLM:
    """
    Returns a PlannerLLM instance.
    Raises RuntimeError if API key is missing (caught by caller for fallback).
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")
    return PlannerLLM()


def run_planner_prompt(llm_instance: PlannerLLM, prompt: str) -> str:
    """
    Convenience wrapper to run a prompt on a PlannerLLM instance.
    """
    return llm_instance.run_prompt(prompt)


# Quick test if this file is run directly
if __name__ == "__main__":
    llm = get_planner_llm()
    test_prompt = "Hello Planner Agent! Summarize your tasks."
    result = run_planner_prompt(llm, test_prompt)
    print("LLM Response:\n", result)

