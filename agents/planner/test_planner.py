from agents.planner.graph import planner_app, PlannerState
from agents.planner.graph import Project

# ----------------------------
# Setup test projects
# ----------------------------
projects = [
    Project(name="Project Alpha", priority=3),
    Project(name="Project Beta", priority=2),
    Project(name="Project Gamma", priority=1)
]

# ----------------------------
# Initialize planner state
# ----------------------------
state = PlannerState(projects=projects)

# ----------------------------
# Run Planner Agent
# ----------------------------
updated_state = planner_app.run(state)

# ----------------------------
# Output results
# ----------------------------
print("\n=== Planner Test Results ===")
print("TOP FOCUS:", updated_state.top_focus)
print("TASKS:")
for idx, task in enumerate(updated_state.constraints.get("tasks", []), start=1):
    print(f"{idx}. {task}")
print("============================\n")

