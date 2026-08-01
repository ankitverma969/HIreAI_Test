from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    # API Keys
    OPENAI_API_KEY: str = Field(default="mock-key-for-local-testing")
    GROQ_API_KEY: str = Field(default="mock-key-for-local-testing")
    GEMINI_API_KEY: str = Field(default="mock-key-for-local-testing")

    # Model Configurations
    MODEL_NAME: str = Field(default="gpt-4o-mini")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")

    # Application settings
    APP_NAME: str = Field(default="Resume Screening Agent")
    APP_VERSION: str = Field(default="1.0.0")
    LOG_LEVEL: str = Field(default="INFO")

    # Environment config
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
