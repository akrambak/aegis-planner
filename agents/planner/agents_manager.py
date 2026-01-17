# agents/planner/agents_manager.py
import asyncio
from typing import List, Dict
from agents.planner.control_plane import control_execute
from agents.planner import memory

class Agent:
    def __init__(self, name: str, allowed_types: List[str]):
        self.name = name
        self.allowed_types = allowed_types
        self.queue = []

    def add_task(self, task: Dict):
        if task['type'] in self.allowed_types:
            self.queue.append(task)
        else:
            # Skip task if agent cannot execute it
            print(f"[{self.name}] Skipping task type: {task['type']}")

    async def run(self, dry_run: bool = False):
        results = []
        for task in self.queue:
            status, output, error = control_execute(task['payload'], dry_run=dry_run)
            memory.log_execution(task['payload'], status, self.name)
            results.append({
                "task": task,
                "status": status,
                "output": output,
                "error": error
            })
        return results

class AgentsManager:
    def __init__(self):
        self.agents = {
            "dev": Agent("Dev Agent", allowed_types=["shell", "python"]),
            "ops": Agent("Ops Agent", allowed_types=["shell", "docker", "git"]),
            "admin": Agent("Admin Agent", allowed_types=["n8n", "api"])
        }

    def distribute_tasks(self, tasks: List[Dict]):
        for task in tasks:
            assigned = False
            for agent in self.agents.values():
                if task['type'] in agent.allowed_types:
                    agent.add_task(task)
                    assigned = True
                    break
            if not assigned:
                print(f"[Manager] Task skipped (no agent): {task['payload']}")

    async def run_all(self, dry_run: bool = False):
        # Run all agents concurrently
        return await asyncio.gather(*(agent.run(dry_run) for agent in self.agents.values()))
