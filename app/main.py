from fastapi import FastAPI
from app.routes.task_routes import router as task_router
from app.routes.system_routes import router as system_router

app = FastAPI(
    title="Multi-Agent Orchestration API",
    version="1.0.0"
)

app.include_router(task_router, prefix="/tasks", tags=["Tasks"])
app.include_router(system_router, prefix="/system", tags=["System"])
