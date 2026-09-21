"""Application settings loaded from environment / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    # Local Whisper
    whisper_model: str = "medium"
    whisper_device: str = "auto"
    whisper_compute_type: str = "float32"
    whisper_language: str = "fa"

    # پیش‌پردازش صدا
    enable_highpass: bool = True
    enable_noise_reduction: bool = True
    enable_normalize: bool = True

    # عمومی
    default_provider: str = "local"
    log_level: str = "INFO"

    # runtime-only
    extra: dict = field(default_factory=dict)


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _env_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on", "بله")


def load_settings(env_file: str | Path | None = ".env") -> Settings:
    if env_file and Path(env_file).exists():
        load_dotenv(env_file, override=False)

    return Settings(
        whisper_model=_env("WHISPER_MODEL", "medium") or "medium",
        whisper_device=_env("WHISPER_DEVICE", "auto") or "auto",
        whisper_compute_type=_env("WHISPER_COMPUTE_TYPE", "float32") or "float32",
        whisper_language=_env("WHISPER_LANGUAGE", "fa") or "fa",
        enable_highpass=_env_bool("ENABLE_HIGHPASS", True),
        enable_noise_reduction=_env_bool("ENABLE_NOISE_REDUCTION", True),
        enable_normalize=_env_bool("ENABLE_NORMALIZE", True),
        default_provider=_env("DEFAULT_PROVIDER", "local") or "local",
        log_level=_env("LOG_LEVEL", "INFO") or "INFO",
    )
