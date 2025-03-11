import os
import pathlib
from functools import lru_cache


class BaseConfig:
    BASE_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent

    HOST_DOMAIN: str = os.environ.get("HOST_DOMAIN")
    ## for async sqlite
    DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/db.sqlite3")
    SYNC_DB_URL: str = os.environ.get("SYNC_DB_URL", f"sqlite:///{BASE_DIR}/db.sqlite3")
    ASYNC_DATABASE_CONNECT_DICT: dict = {
        # https://stackoverflow.com/questions/75477373/sqlalchemy-is-slow-when-doing-query-the-first-time
        "server_settings": { "jit": "off" }
    }
    SYNC_DATABASE_CONNECT_DICT: dict = {}
    # If having problems with async, make sure always eager is set to false
    CELERY_broker_url: str = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    result_backend: str = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")

    # Embedding APIs
    VOYAGE_API_KEY: str = os.environ.get("VOYAGE_API_KEY")

    # Models
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY")
    
    AUTH_SECRET: str = os.environ.get("AUTH_SECRET", "PLACEHOLDER")
    ACCESS_TOKEN_LIFETIME: int = int(os.environ.get("ACCESS_TOKEN_LIFETIME", "3600"))
    REFRESH_TOKEN_LIFETIME: int = int(os.environ.get("REFRESH_TOKEN_LIFETIME", "86400"))
    # Take care reusing volumes with docker-compose if db already exists and you change the connection URL
    # https://stackoverflow.com/questions/68626017/docker-compose-psql-error-fatal-role-postgres-does-not-exist


# class DevelopmentConfig(BaseConfig):
#     ENVIRONMENT: str = "development"

@lru_cache()
def get_settings():
    # config_cls_dict = {"development": DevelopmentConfig }
    # config_name = os.environ.get("FASTAPI_CONFIG", "development")
    # config_cls = config_cls_dict[config_name]
    
    config_cls = BaseConfig
    return config_cls()


settings = get_settings()