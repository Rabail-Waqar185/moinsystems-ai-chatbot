from fastapi import APIRouter

from app.db.session import database_is_ready

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    db_ready = database_is_ready()
    return {
        "status": "ok" if db_ready else "degraded",
        "app": "up",
        "database": "up" if db_ready else "down",
    }
