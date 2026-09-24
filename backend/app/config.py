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
        return (
            os.getenv("SDIP_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or "sqlite:///./scoreboard.db"
        )

    # Static Files (Frontend)
    @property
    def STATIC_DIR(self) -> str | None:
        custom_dir = os.getenv("STATIC_DIR")
        if custom_dir and os.path.isdir(custom_dir):
            return custom_dir
        if os.path.isdir("/app/static"):
            return "/app/static"
        local_candidate = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
        )
        if os.path.isdir(local_candidate):
            return local_candidate
        return None

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
