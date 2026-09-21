"""Provider factory — only Local Whisper is supported."""

from __future__ import annotations

from app.config.settings import Settings
from app.speech.base import SpeechToTextProvider


def create_provider(name: str, settings: Settings) -> SpeechToTextProvider:
    # همیشه Local — نام ورودی نادیده گرفته می‌شود
    from .local_whisper import LocalWhisperProvider

    return LocalWhisperProvider(settings)
