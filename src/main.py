from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from src.config.settings import settings
from src.db.session import engine
from src.db.models import Base
from src.api.v1.endpoints import health,products,users,subscriptions,price_history
from src.services.scheduler import start_scheduler, scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S")

logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    start_scheduler()
    yield
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Routerek regisztrálása
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health Check"])
app.include_router(products.router, prefix=f"{settings.API_V1_STR}/products",tags=["Products"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(subscriptions.router, prefix=f"{settings.API_V1_STR}/subscriptions", tags=["Subscriptions"])
app.include_router(price_history.router, prefix=f"{settings.API_V1_STR}/history",tags={"Price History"})

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API!"}