"""GET /health — liveness probe."""
import platform
import sys

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "python": sys.version,
        "platform": platform.platform(),
    }
