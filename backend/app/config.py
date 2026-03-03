from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    assistant_name: str
    cors_origins: tuple[str, ...]
    trusted_hosts: tuple[str, ...]
    single_user_mode: bool


def _split_csv(value: str) -> tuple[str, ...]:
    items = [item.strip() for item in value.split(",")]
    return tuple(item for item in items if item)


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_settings() -> Settings:
    _load_env_file()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        assistant_name=os.getenv("ASSISTANT_NAME", "Alpha"),
        cors_origins=_split_csv(
            os.getenv(
                "CORS_ORIGINS",
                "http://localhost:8000,http://127.0.0.1:8000",
            )
        ),
        trusted_hosts=_split_csv(
            os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,[::1]")
        ),
        single_user_mode=_as_bool(os.getenv("SINGLE_USER_MODE"), True),
    )
