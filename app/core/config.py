#!/usr/bin/env python3

"""This module contains the configurations for the API."""
import os
from datetime import datetime, timedelta, timezone

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Defines the configurations for the hospital backend system."""

    # app variables
    app_name: str = "Hospital Backend System"
    app_env: str = "development"
    app_port: int = 8000

    # API version
    api_version: str = "v1"

    # Login route
    login_route: str = f"/api/{api_version}/auth/login"

    # database variables
    db_type: str = "postgresql"
    db_test_url: str = ""
    db_url: str = ""
    db_user: str = ""
    db_name: str = "hospital_db"
    db_password: str = ""
    db_port: int = 0  # When using SQLite, this is not needed
    db_host: str = "localhost"

    # authentication and security
    secret_key: str
    access_token_expire_minutes: int = 60
    access_token_duration: datetime = datetime.now(timezone.utc) + timedelta(
        minutes=access_token_expire_minutes
    )

    hashing_algorithm: str = "HS256"
    minimum_password_length: int = 8
    maximum_password_length: int = 15

    # LLM integration
    llm_api_key: str
    llm_model: str

    # Encryption settings. This is used to encrypt doctor notes
    encryption_key: str
    encryption_algorithm: str

    # Redis (for Caching & Background Jobs)
    redis_host: str = "localhost"
    redis_port: int = 6376
    redis_db: int = 0

    # pagination
    pagination_limit: int = 100
    pagination_default_page: int = 10

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

# Setup database for each environment
if settings.db_type == "sqlite":
    db_path = f"{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))}"
    if settings.app_env == "development":
        settings.db_url = f"sqlite:///{db_path}/{settings.db_name}_development.db"
        settings.db_test_url = f"sqlite:///{db_path}/{settings.db_name}_test.db"
    else:
        settings.db_url = f"sqlite:///{db_path}/{settings.db_name}_production.db"
elif settings.app_env == "development":
    settings.db_url = settings.db_url or (
        f"{settings.db_type}://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}_development"
    )
    settings.db_test_url = (
        f"{settings.db_type}://{settings.db_user}_test:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}_test"
    )
else:
    settings.db_url = settings.db_url or (
        f"{settings.db_type}://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}_production"
    )
