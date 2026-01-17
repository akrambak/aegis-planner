def score_project(project):
    score = 0

    if project.status != "active":
        return -100

    if project.blocker:
        score -= 2

    score += max(0, 5 - project.priority)

    return score
