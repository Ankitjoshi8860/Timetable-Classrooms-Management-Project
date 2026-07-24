"""Environment-aware Flask configuration."""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "env", override=False)


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    APP_NAME = "Timetable Classroom Management"
    JSON_SORT_KEYS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-only-secret"
    SESSION_COOKIE_SECURE = False


def get_config(config_name=None):
    """Return the requested configuration class.

    FLASK_ENV is intentionally not used because it was removed from newer
    Flask versions. APP_CONFIG remains explicit and works across environments.
    """
    name = (config_name or os.getenv("APP_CONFIG", "development")).lower()
    configurations = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    try:
        selected = configurations[name]
    except KeyError as exc:
        supported = ", ".join(sorted(configurations))
        raise ValueError(f"Unsupported APP_CONFIG '{name}'. Use: {supported}") from exc

    if name == "production":
        secret_key = os.getenv("SECRET_KEY", "")
        if (
            len(secret_key) < 32
            or secret_key.startswith("replace-with")
            or secret_key == "test-only-secret"
        ):
            raise RuntimeError(
                "Production requires a SECRET_KEY of at least 32 characters; "
                "do not use a placeholder or test secret."
            )
    return selected
