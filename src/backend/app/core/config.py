from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/finanlove"
    )

    JWT_SECRET: str = "development-only-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.APP_ENV.lower() in {"production", "prod"}:
            if len(self.JWT_SECRET) < 32 or self.JWT_SECRET in {
                "development-only-change-me",
                "your-super-secret-key-change-it-in-production",
            }:
                raise ValueError(
                    "JWT_SECRET must be a unique value of at least 32 characters"
                    " in production"
                )
        return self


settings = Settings()
