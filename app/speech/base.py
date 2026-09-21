"""Abstract SpeechToText provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class TranscriptionResult:
    text: str
    language: str = ""
    duration: float = 0.0
    provider: str = ""


class SpeechToTextProvider(ABC):
    """All STT backends must implement this interface."""

    name: str = "base"

    @abstractmethod
    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: str | None = None,
        progress_cb=None,  # optional callable(str)
    ) -> TranscriptionResult:
        """Transcribe mono float32 audio. Must be thread-safe."""
        raise NotImplementedError

    def warmup(self, progress_cb=None) -> None:  # optional
        return None

    def close(self) -> None:
        return None
