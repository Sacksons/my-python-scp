"""
Centralized configuration for the Kazi backend application.
All sensitive values should be set via environment variables.
"""

import os
from functools import lru_cache
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Database - Direct connection (preferred for production)
    DATABASE_URL: Optional[str] = os.environ.get("DATABASE_URL")

    # Database - SSH Tunnel (for PythonAnywhere or similar)
    PA_USERNAME: Optional[str] = os.environ.get("PA_USERNAME")
    PA_PASSWORD: Optional[str] = os.environ.get("PA_PASSWORD")
    PG_HOST: Optional[str] = os.environ.get("PG_HOST")
    PG_PORT: int = int(os.environ.get("PG_PORT", "5432"))
    PG_USER: Optional[str] = os.environ.get("PG_USER")
    PG_PASS: Optional[str] = os.environ.get("PG_PASS")
    PG_DB: Optional[str] = os.environ.get("PG_DB")

    # SSH Tunnel settings
    SSH_TIMEOUT: float = float(os.environ.get("SSH_TIMEOUT", "10.0"))
    TUNNEL_TIMEOUT: float = float(os.environ.get("TUNNEL_TIMEOUT", "10.0"))

    # Application
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    ALLOWED_ORIGINS: list[str] = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    @property
    def use_ssh_tunnel(self) -> bool:
        """Determine if SSH tunnel should be used based on available config."""
        return bool(self.PA_USERNAME and self.PA_PASSWORD and not self.DATABASE_URL)

    def validate(self) -> None:
        """Validate required configuration is present."""
        if not self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY environment variable is required. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )

        if not self.DATABASE_URL and not self.use_ssh_tunnel:
            if not all([self.PG_USER, self.PG_PASS, self.PG_DB, self.PG_HOST]):
                raise ValueError(
                    "Database configuration required. Set DATABASE_URL or "
                    "PG_USER, PG_PASS, PG_DB, PG_HOST environment variables."
                )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
