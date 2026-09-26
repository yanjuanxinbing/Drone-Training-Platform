"""Application settings (env-driven)."""
from __future__ import annotations

import os
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

    # ProjectAirSim (UE 5.7)
    airsim_ip: str = "127.0.0.1"               # legacy alias
    airsim_port: int = 8989                    # legacy alias → port_topics
    projectairsim_host: str = "127.0.0.1"
    projectairsim_port_topics: int = 8989
    projectairsim_port_services: int = 8990
    projectairsim_scene: str = "scene_basic_drone.jsonc"
    projectairsim_drone: str = "Drone1"
    projectairsim_camera: str = "front_center"

    # Map cache
    nfz_cache_ttl_seconds: int = 600


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Pull runtime overrides from os.environ (the existing config.json also
    # carries jwt_secret etc., but env wins).
    return Settings()


settings = get_settings()