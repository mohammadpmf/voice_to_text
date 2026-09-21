"""Local Whisper provider using faster-whisper.

Prefers a locally downloaded model in ./models/faster-whisper-<size>.
Falls back to Hugging Face download if the local model is missing.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import numpy as np

from app.audio.processor import preprocess
from app.config.settings import Settings
from app.speech.base import SpeechToTextProvider, TranscriptionResult
from app.utils.logger import get_logger
from app.utils.text_utils import normalize_persian

log = get_logger(__name__)

MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MODELS_DIR = _PROJECT_ROOT / "models"

# پرامپت اولیه برای راهنمایی Whisper روی فارسی
_INITIAL_PROMPT_FA = (
    "این یک فایل صوتی فارسی است. متن با علائم نگارشی صحیح نوشته می‌شود."
)
_INITIAL_PROMPT_EN = "This is an English audio transcription with correct punctuation."


def _local_model_path(model_size: str) -> Path:
    return _MODELS_DIR / f"faster-whisper-{model_size}"


def _is_model_ready(path: Path) -> bool:
    if not path.is_dir():
        return False
    has_bin = any(path.glob("*.bin"))
    has_cfg = (path / "config.json").exists()
    return has_bin and has_cfg


class LocalWhisperProvider(SpeechToTextProvider):
    name = "local"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = None
        self._lock = threading.Lock()
        self._loaded_signature: tuple[str, str, str] | None = None

    # ---------- internal ----------
    def _resolve_device(self) -> tuple[str, str]:
        device = self._settings.whisper_device
        compute = self._settings.whisper_compute_type
        if device == "auto":
            try:
                import torch  # type: ignore

                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                try:
                    import ctranslate2

                    device = (
                        "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
                    )
                except Exception:
                    device = "cpu"
        if compute == "auto":
            compute = "float16" if device == "cuda" else "int8"
        return device, compute

    def _resolve_model_source(self, model_size: str) -> tuple[str, bool]:
        local = _local_model_path(model_size)
        if _is_model_ready(local):
            return str(local), True
        return model_size, False

    def _ensure_model(
        self, model_size: str, progress_cb: Callable[[str], None] | None
    ) -> None:
        device, compute = self._resolve_device()
        signature = (model_size, device, compute)
        with self._lock:
            if self._model is not None and self._loaded_signature == signature:
                return

            from faster_whisper import WhisperModel

            source, is_local = self._resolve_model_source(model_size)

            if is_local:
                if progress_cb:
                    progress_cb(
                        f"بارگذاری مدل «{model_size}» از پوشه‌ی models روی {device} ({compute})…"
                    )
                log.info("Loading local model %s on %s (%s)", source, device, compute)
                self._model = WhisperModel(source, device=device, compute_type=compute)
            else:
                if progress_cb:
                    progress_cb(
                        f"⚠️ مدل «{model_size}» در پوشه‌ی models پیدا نشد. "
                        f"`python download_model.py {model_size}` را اجرا کنید. "
                        "اکنون از Hugging Face دانلود می‌شود…"
                    )
                log.warning("Local model missing; downloading %s", model_size)
                _MODELS_DIR.mkdir(parents=True, exist_ok=True)
                self._model = WhisperModel(
                    model_size,
                    device=device,
                    compute_type=compute,
                    download_root=str(_MODELS_DIR),
                )

            self._loaded_signature = signature
            if progress_cb:
                progress_cb("مدل آماده است.")

    # ---------- public ----------
    def warmup(self, progress_cb: Callable[[str], None] | None = None) -> None:
        self._ensure_model(self._settings.whisper_model, progress_cb)

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: str | None = None,
        progress_cb: Callable[[str], None] | None = None,
    ) -> TranscriptionResult:
        model_size = self._settings.whisper_model
        self._ensure_model(model_size, progress_cb)

        lang = (
            language
            if language and language != "auto"
            else self._settings.whisper_language
        )
        if lang == "auto":
            lang = None

        # --- پیش‌پردازش ---
        if progress_cb:
            progress_cb("پیش‌پردازش صدا (نرمال‌سازی و کاهش نویز)…")

        audio = preprocess(
            audio,
            sample_rate=sample_rate,
            enable_highpass=self._settings.enable_highpass,
            enable_noise_reduction=self._settings.enable_noise_reduction,
            enable_normalize=self._settings.enable_normalize,
        )

        if progress_cb:
            progress_cb("در حال تبدیل گفتار به متن…")

        # --- پرامپت اولیه بر اساس زبان ---
        if lang == "en":
            initial_prompt = _INITIAL_PROMPT_EN
        else:
            initial_prompt = _INITIAL_PROMPT_FA

        assert self._model is not None
        segments, info = self._model.transcribe(
            audio,
            language=lang,
            task="transcribe",
            beam_size=5,
            best_of=5,
            patience=1.0,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
            condition_on_previous_text=False,
            initial_prompt=initial_prompt,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
                threshold=0.5,
            ),
        )

        parts: list[str] = []
        for seg in segments:
            text = (seg.text or "").strip()
            if text:
                parts.append(text)

        full = " ".join(parts)
        full = normalize_persian(full)

        return TranscriptionResult(
            text=full,
            language=getattr(info, "language", lang or ""),
            duration=float(getattr(info, "duration", 0.0) or 0.0),
            provider=self.name,
        )

    def close(self) -> None:
        with self._lock:
            self._model = None
            self._loaded_signature = None
