"""
Application configuration and settings.
"""

from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Content Understanding API"

    # CORS Configuration - store as string, parse to list via computed field
    allowed_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        validation_alias="ALLOWED_ORIGINS",
    )

    @computed_field
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string."""
        return [
            origin.strip()
            for origin in self.allowed_origins_str.split(",")
            if origin.strip()
        ]

    # Azure Content Understanding Configuration
    AZURE_CONTENT_UNDERSTANDING_ENDPOINT: str = ""
    AZURE_CONTENT_UNDERSTANDING_KEY: str = ""
    AZURE_CONTENT_UNDERSTANDING_API_VERSION: str = ""
    AZURE_CONTENT_UNDERSTANDING_ANALYZER_NAME: str = ""

    # PhenoML Construe Configuration (placeholder)
    PHENOML_API_ENDPOINT: str = ""
    PHENOML_API_KEY: str = ""

    # BackBlaze B2 Storage Configuration
    B2_KEY_ID: str = ""
    B2_APPLICATION_KEY: str = ""
    B2_BUCKET_NAME: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
