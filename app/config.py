import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="sqlite:///./projecthub.db",
        description="Database connection URL (PostgreSQL in production/dev, SQLite in local/test)"
    )
    SECRET_KEY: str = Field(
        default="a_very_secret_key_at_least_32_characters_long_for_jwt_auth_123",
        description="Secret key for JWT token encoding/decoding"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT signature algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="Access token expiration in minutes"
    )
    ADMIN_EMAIL: str = Field(
        default="admin@projecthub.edu",
        description="Default administrator email"
    )
    ADMIN_PASSWORD: str = Field(
        default="AdminPass123!",
        description="Default administrator password"
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Application environment (development, production, testing)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # In non-testing environments, ensure key is sufficiently secure and not blank
        env = os.getenv("ENVIRONMENT", "development")
        if env != "testing":
            if not v or len(v.strip()) < 16:
                raise ValueError("SECRET_KEY must be at least 16 characters long.")
            if v == "insecure_default_key":
                raise ValueError("Default insecure SECRET_KEY cannot be used outside test mode.")
        return v


settings = Settings()
