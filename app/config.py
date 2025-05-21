import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class Settings(BaseSettings):
    auth_token: str

    class Config:
        env_file = ".env"


try:
    settings = Settings()
    logger.info("Settings successfully loaded from .env file.")
except Exception as e:
    logger.exception("Failed to load settings: %s", e)
