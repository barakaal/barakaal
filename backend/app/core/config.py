from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Dropship Company OS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/barakaal"
    REDIS_URL: str = "redis://localhost:6379/0"

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_PROVIDER: str = "anthropic"
    AI_MODEL: str = "claude-sonnet-4-6"

    FRONTEND_URL: str = "http://localhost:3000"

    HUMAN_APPROVAL_REQUIRED: bool = True
    MAX_AUTO_SPEND_USD: float = 0.0

    WEEKLY_WORKFLOW_CRON: str = "0 9 * * 1"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
