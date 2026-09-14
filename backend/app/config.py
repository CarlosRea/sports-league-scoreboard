import logging
import os
import secrets

logger = logging.getLogger("uvicorn")


class Settings:
    PROJECT_NAME: str = "Sports League Scoreboard API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # JWT & Auth
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("DATABASE_URL", "sqlite:///./scoreboard.db")

    def __init__(self):
        self._ephemeral_secret: str | None = None

    @property
    def JWT_SECRET(self) -> str:
        env_secret = os.getenv("JWT_SECRET_KEY")
        if env_secret:
            return env_secret

        if not self._ephemeral_secret:
            logger.warning(
                "JWT_SECRET_KEY not found in environment. Using ephemeral random key for instance isolation."
            )
            self._ephemeral_secret = secrets.token_hex(32)
        return self._ephemeral_secret


settings = Settings()
