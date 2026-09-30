"""Application settings (env-driven)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DRONE_", env_file=".env", extra="ignore")

    project_name: str = "Drone Training Platform API"
    version: str = "0.1.0"

    # Auth
    jwt_secret: str = "drone-training-platform-secret-key-change-in-production"
    jwt_alg: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]

    # AirSim
    airsim_ip: str = "127.0.0.1"
    airsim_port: int = 41451

    # UE4.27 Pixel Streaming (Cirrus) — points at the local signaling server.
    # Default matches the convention used by `test.py` at the repo root.
    pixel_streaming_url: str = "http://localhost/"

    # Map cache
    nfz_cache_ttl_seconds: int = 600


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Pull runtime overrides from os.environ (the existing config.json also
    # carries jwt_secret etc., but env wins).
    return Settings()


settings = get_settings()