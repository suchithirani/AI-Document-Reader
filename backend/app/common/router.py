from fastapi import APIRouter

from backend.app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}
