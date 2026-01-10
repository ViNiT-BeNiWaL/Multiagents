from fastapi import APIRouter
from app.schemas.task_schema import TaskRequest
from core.orchestrator_engine import OrchestratorEngine

router = APIRouter()
engine = OrchestratorEngine()


@router.post("/execute")
def execute_task(payload: TaskRequest):
    result = engine.execute(payload.task, payload.context)
    return {
        "success": True,
        "data": result
    }
