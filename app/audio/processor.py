"""Audio preprocessing: gain normalization, high-pass filter, noise reduction."""

from __future__ import annotations

import numpy as np

from app.utils.logger import get_logger

log = get_logger(__name__)


def normalize_gain(
    audio: np.ndarray,
    target_peak: float = 0.95,
    max_gain_db: float = 20.0,
) -> np.ndarray:
    """Normalize audio so its peak reaches target_peak.

    Amplification is capped at max_gain_db to avoid boosting pure silence.
    """
    if audio.size == 0:
        return audio
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-6:
        return audio

    target_gain = target_peak / peak
    max_gain = 10 ** (max_gain_db / 20.0)
    gain = min(target_gain, max_gain)

    if gain <= 1.02:  # اگر تقریباً نرمال است، کاری نکن
        return audio

    log.debug("Normalize: peak=%.4f gain=%.2fx", peak, gain)
    return (audio * gain).astype(np.float32, copy=False)


def high_pass_filter(
    audio: np.ndarray,
    sample_rate: int = 16000,
    cutoff_hz: float = 80.0,
) -> np.ndarray:
    """Remove low-frequency rumble (fan, AC, table vibration)."""
    if audio.size < 16:
        return audio
    try:
        from scipy import signal as sp_signal

        nyq = sample_rate / 2.0
        wn = max(0.001, min(0.99, cutoff_hz / nyq))
        b, a = sp_signal.butter(4, wn, btype="highpass")
        filtered = sp_signal.filtfilt(b, a, audio.astype(np.float32))
        return filtered.astype(np.float32, copy=False)
    except Exception:
        log.exception("High-pass filter failed; returning original audio")
        return audio


def reduce_noise_light(
    audio: np.ndarray,
    sample_rate: int = 16000,
    prop_decrease: float = 0.75,
) -> np.ndarray:
    """Light spectral-gating noise reduction (stationary noise only)."""
    if audio.size < sample_rate // 2:
        return audio  # کمتر از نیم ثانیه
    try:
        import noisereduce as nr

        reduced = nr.reduce_noise(
            y=audio,
            sr=sample_rate,
            stationary=True,
            prop_decrease=prop_decrease,
            n_fft=1024,
        )
        return np.asarray(reduced, dtype=np.float32)
    except Exception:
        log.exception("Noise reduction failed; returning original audio")
        return audio


def preprocess(
    audio: np.ndarray,
    sample_rate: int = 16000,
    enable_highpass: bool = True,
    enable_noise_reduction: bool = True,
    enable_normalize: bool = True,
) -> np.ndarray:
    """Full preprocessing pipeline: high-pass -> denoise -> normalize."""
    out = np.asarray(audio, dtype=np.float32)

    if out.size == 0:
        return out

    # حذف DC offset
    out = out - float(np.mean(out))

    if enable_highpass:
        out = high_pass_filter(out, sample_rate, cutoff_hz=80.0)

    if enable_noise_reduction:
        out = reduce_noise_light(out, sample_rate, prop_decrease=0.75)

    if enable_normalize:
        out = normalize_gain(out, target_peak=0.95, max_gain_db=20.0)

    # جلوگیری از clip نهایی
    np.clip(out, -1.0, 1.0, out=out)
    return out
