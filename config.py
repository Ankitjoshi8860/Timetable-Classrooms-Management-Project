"""Environment-aware Flask configuration."""

import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


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
        return configurations[name]
    except KeyError as exc:
        supported = ", ".join(sorted(configurations))
        raise ValueError(f"Unsupported APP_CONFIG '{name}'. Use: {supported}") from exc
