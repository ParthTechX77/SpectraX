from fastapi import FastAPI
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.redis_client import redis_client


app = FastAPI(
    title=f"{settings.app_name} API",
    description=(
        "Explainable multimodal AI forensics platform "
        "for deepfake detection, provenance, and digital evidence."
    ),
    version=settings.app_version,
)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    database_status = "healthy"
    redis_status = "healthy"

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        database_status = "unhealthy"

    try:
        await redis_client.ping()
    except Exception:
        redis_status = "unhealthy"

    overall_status = (
        "healthy"
        if database_status == "healthy"
        and redis_status == "healthy"
        else "degraded"
    )

    return {
        "status": overall_status,
        "service": settings.app_name,
        "version": settings.app_version,
        "dependencies": {
            "database": database_status,
            "redis": redis_status,
        },
    }