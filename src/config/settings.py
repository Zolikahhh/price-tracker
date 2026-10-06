from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Price Tracker API"
    VERSION: str = "0.1.0"
    
    # PostgreSQL adatok
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgrespassword"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "price_tracker"
    
    # Összeállítjuk az aszinkron PostgreSQL kapcsolódási karakterláncot
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis beállítások
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Megmondjuk a Pydantic-nak, hogy a .env fájlt használja
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Példányosítjuk, hogy bárhonnan importálható legyen: `from src.config.settings import settings`
settings = Settings()