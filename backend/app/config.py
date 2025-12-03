"""
Application configuration and settings.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Content Understanding API"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Azure Content Understanding Configuration
    AZURE_CONTENT_UNDERSTANDING_ENDPOINT: str = ""
    AZURE_CONTENT_UNDERSTANDING_KEY: str = ""
    
    # PhenoML Construe Configuration (placeholder)
    PHENOML_API_ENDPOINT: str = ""
    PHENOML_API_KEY: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()

