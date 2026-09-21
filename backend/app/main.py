from fastapi import FastAPI
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

app.include_router(api_router)