from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.router import api_router
from app.database import engine


app = FastAPI(
    title="SpectraX API",
    description=(
        "Explainable multimodal AI forensics platform "
        "for deepfake detection, provenance, and digital evidence."
    ),
    version="0.1.0",
)


app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": "SpectraX",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SpectraX API",
        "version": "0.1.0",
    }


@app.get("/health/database")
async def database_health_check():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected",
        "result": result.scalar(),
    }