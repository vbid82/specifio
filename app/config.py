from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str
    database_url_sync: str = ""

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 168  # 7 days
    jwt_secret_rotated_at: int = 0
    magic_link_expiry_minutes: int = 30

    # Email
    resend_api_key: str = ""
    email_from: str = "hello@specifio.eu"
    email_from_name: str = "Specifio"
    magic_link_base_url: str = "https://specifio.eu/auth/verify"

    # HubSpot
    hubspot_access_token: str = ""

    # App
    app_env: str = "production"
    app_url: str = "https://specifio.eu"
    api_url: str = "https://api.specifio.eu"
    cors_origins: str = "https://specifio.eu"
    frontend_base_url: str = "https://specifio.eu"

    # Rate limits
    registration_rate_limit_per_ip: int = 5
    magic_link_rate_limit_per_email: int = 3

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
