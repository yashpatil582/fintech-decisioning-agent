"""Health and readiness endpoints."""

from fastapi import APIRouter, Request
from app.schemas.decision import HealthStatus
from app.chains.bedrock_llm import ping_bedrock

health_router = APIRouter()


@health_router.get("/", response_model=HealthStatus)
async def health(request: Request) -> HealthStatus:
    agent = getattr(request.app.state, "agent", None)
    return HealthStatus(
        status="ok",
        bedrock_connected=ping_bedrock(),
        vector_store_ready=agent is not None and agent.retriever is not None,
    )


@health_router.get("/ready")
async def readiness(request: Request):
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        return {"ready": False}
    return {"ready": True}
