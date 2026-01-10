from pydantic import BaseModel
from typing import Dict, Any, Optional


class TaskRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
