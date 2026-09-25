from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,
)