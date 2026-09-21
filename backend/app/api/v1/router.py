from fastapi import APIRouter

from app.api.v1.cases import router as cases_router


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(cases_router)

