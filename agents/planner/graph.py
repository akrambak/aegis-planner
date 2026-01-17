import json
from agents.planner.llm import get_planner_llm, run_planner_prompt

# ----------------------------
# Dummy project state classes
# ----------------------------
class Project:
    def __init__(self, name, current_focus="", status="active", priority=1):
        self.name = name
        self.current_focus = current_focus
        self.status = status
        self.priority = priority


class PlannerState:
    """
    Stores all projects and current planner constraints.
    """
    def __init__(self, projects=None, constraints=None):
        self.projects = projects or []
        self.constraints = constraints or {}
        self.top_focus = None  # The main project to focus on today


# ----------------------------
# Planner Graph Logic
# ----------------------------
def score_project(project):
    """
    Simple scoring function based on priority.
    Higher priority means higher score.
    """
    return project.priority


# Initialize LLM
llm = get_planner_llm()


def plan_day(state: PlannerState):
    """
    Rank projects and generate tasks using LLM
    """
    # Filter active projects and sort by priority
    ranked = sorted(
        [p for p in state.projects if p.status == "active"],
        key=lambda p: score_project(p),
        reverse=True
    )

    if not ranked:
        state.top_focus = "No active projects today."
        state.constraints["tasks"] = []
        return state

    top_project = ranked[0]

    # Build context for LLM
    context = {
        "projects": [
            {
                "name": p.name,
                "focus": p.current_focus,
                "status": p.status,
                "priority": p.priority
            } for p in ranked
        ],
        "constraints": state.constraints
    }

    prompt = (
        "You are a personal planner AI.\n"
        "Given the projects below and current constraints, "
        "decide the top project to focus on today and generate a task list.\n"
        "Output JSON in the format:\n"
        '{"project": "<top_project_name>", "reason": "<why>", "tasks": ["task1", "task2"]}\n\n'
        "Projects:\n" + json.dumps(context, indent=2)
    )

    # Run LLM
    try:
        response_text = run_planner_prompt(llm, prompt)
        decision = json.loads(response_text)
    except Exception as e:
        # fallback if LLM fails
        decision = {
            "project": top_project.name,
            "reason": "LLM failed, using priority fallback",
            "tasks": ["Define tasks manually"]
        }

    # Update state
    state.top_focus = f"{decision['project']} — {decision['reason']}"
    state.constraints["tasks"] = [
        {"task_type": "shell", "payload": task}
        if isinstance(task, str)
        else task
        for task in decision["tasks"]
    ]

    return state


# ----------------------------
# Example Planner Graph API
# ----------------------------
class StateGraph:
    """
    Very simple planner graph wrapper
    """
    def __init__(self, state_cls):
        self.state_cls = state_cls
        self.entry_point = None
        self.nodes = {}

    def add_node(self, name, func):
        self.nodes[name] = func

    def set_entry_point(self, name):
        self.entry_point = name

    def compile(self):
        return self

    def run(self, state):
        if self.entry_point and self.entry_point in self.nodes:
            return self.nodes[self.entry_point](state)
        else:
            raise RuntimeError("No valid entry point set for the graph.")


# ----------------------------
# Instantiate Planner Graph
# ----------------------------
graph = StateGraph(PlannerState)
graph.add_node("plan_day", plan_day)
graph.set_entry_point("plan_day")
planner_app = graph.compile()


# ----------------------------
# Quick test if run directly
# ----------------------------
if __name__ == "__main__":
    projects = [
        Project("Project Alpha", priority=3),
        Project("Project Beta", priority=2),
        Project("Project Gamma", priority=1)
    ]
    state = PlannerState(projects=projects)
    updated_state = planner_app.run(state)
    print("TOP FOCUS:", updated_state.top_focus)
    print("TASKS:", updated_state.constraints["tasks"])

