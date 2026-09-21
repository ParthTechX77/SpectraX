from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.25.94.127:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    health = {
        "status": "healthy",
        "database": "healthy",
        "redis": "healthy",
    }

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        health["database"] = "unhealthy"

    try:
        await redis_client.ping()
    except Exception:
        health["redis"] = "unhealthy"

    if (
        health["database"] != "healthy"
        or health["redis"] != "healthy"
    ):
        health["status"] = "unhealthy"

    return health

app.include_router(api_router)
