from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from src.config.settings import settings

# Aszinkron PostgreSQL Engine létrehozása
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future = True  # Kiírja az SQL lekérdezéseket a terminálba (fejlesztéshez)
)

# Munkamenet-gyár (Session factory)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Ősosztály az ORM modellekhez
class Base(DeclarativeBase):
    pass

# FastAPI Dependency Injection-höz használt DB session provider
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Helper függvény az adatbázis táblák automatikus létrehozásához
async def init_db():
    async with engine.begin() as conn:
        from src.db.models import Base
        await conn.run_sync(Base.metadata.create_all)
