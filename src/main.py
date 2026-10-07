from fastapi import FastAPI
from src.config.settings import settings
from src.api.v1.endpoints import health,products,users

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Routerek regisztrálása
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health Check"])
app.include_router(products.router, prefix=f"{settings.API_V1_STR}/products",tags=["Products"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API!"}