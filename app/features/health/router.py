import logging
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str = "0.1.0"
    llm_provider: str
    checks: dict[str, Literal["ok", "error"]]


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    from app.config import Settings
    
    settings: Settings = request.app.state.settings
    checks: dict[str, Literal["ok", "error"]] = {}
    
    try:
        if settings.gemini_api_key:
            checks["config"] = "ok"
        else:
            checks["config"] = "error"
            logger.warning("GEMINI_API_KEY not configured")
    except Exception as e:
        checks["config"] = "error"
        logger.error(f"Config check failed: {e}")
    
    try:
        from app.ai.registry import LLMRegistry
        LLMRegistry(settings).get(settings.llm_provider)
        checks["llm"] = "ok"
    except Exception as e:
        checks["llm"] = "error"
        logger.error(f"LLM provider check failed: {e}")
    
    status: Literal["ok", "degraded"] = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    
    return HealthResponse(
        status=status,
        llm_provider=settings.llm_provider,
        checks=checks,
    )


@router.get("/health/ready")
async def readiness(request: Request) -> dict[str, str]:
    health_result = await health(request)
    if health_result.status == "ok":
        return {"status": "ready"}
    raise Exception("Service not ready")


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """
    Kubernetes liveness probe - сервис жив.
    """
    return {"status": "alive"}
