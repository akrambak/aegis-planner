from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import date

class ProjectState(BaseModel):
    name: str
    status: str               # active | paused | killed
    priority: int             # 1 = highest
    current_focus: Optional[str] = None
    blocker: Optional[str] = None

class PlannerState(BaseModel):
    today: date
    top_focus: str
    projects: List[ProjectState]
    constraints: Dict[str, str]
