from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_MOCK_SENTINEL = "mock-key-for-local-testing"


class Settings(BaseSettings):
    """Application configuration settings."""

    # API Keys
    OPENAI_API_KEY: str = Field(default=_MOCK_SENTINEL)
    GROQ_API_KEY: str = Field(default=_MOCK_SENTINEL)
    GEMINI_API_KEY: str = Field(default=_MOCK_SENTINEL)

    # Custom Gemini API base URL (e.g. for Vertex AI or custom gateway testing)
    GEMINI_API_BASE: str | None = Field(default=None)

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

    # LLM feature controls
    ENABLE_LLM: bool = Field(default=True)
    # Comma-separated or list of allowed providers: openai, gemini, groq
    ALLOWED_LLM_PROVIDERS: list[str] = Field(default_factory=lambda: ["openai", "gemini", "groq"])

    def is_mock_key(self, key_value: str) -> bool:
        """Returns True when a key is a placeholder / empty mock value."""
        return (
            not key_value
            or key_value == _MOCK_SENTINEL
            or "mock" in key_value.lower()
        )

    # Known Gemini model options (frontend and backend may refer to this)
    GEMINI_MODELS: list[str] = Field(default_factory=lambda: [
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
    ])


settings = Settings()
