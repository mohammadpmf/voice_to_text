"""Microphone recorder using sounddevice.

Thread-safe start/stop. Provides both a continuous monitor stream
(for the VU meter when idle) and a recording stream. The recording
callback also updates the level so the VU meter stays alive while
recording.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

import numpy as np
import sounddevice as sd

from app.utils.logger import get_logger

log = get_logger(__name__)

TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1


@dataclass
class RecordingResult:
    samples: np.ndarray  # float32 mono @ 16kHz
    sample_rate: int
    duration: float
    started_at: float = field(default=0.0)
    stopped_at: float = field(default=0.0)


def _rms(samples: np.ndarray) -> float:
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(samples.astype(np.float32, copy=False)))))


class AudioRecorder:
    """Records microphone audio into an in-memory buffer.

    Also provides a lightweight level-monitoring stream so the UI can
    show whether the selected microphone is actually picking up sound.
    While recording, the level is computed from the recording stream
    itself, so the VU meter keeps working.
    """

    def __init__(self) -> None:
        # recording
        self._stream: sd.InputStream | None = None
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._recording = False
        self._start_time = 0.0

        # monitoring
        self._mon_stream: sd.InputStream | None = None
        self._mon_level: float = 0.0
        self._mon_lock = threading.Lock()

    # ---------- properties ----------
    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def is_monitoring(self) -> bool:
        return self._mon_stream is not None

    @property
    def start_time(self) -> float:
        return self._start_time

    # ---------- recording ----------
    def start(
        self,
        device_index: int | None = None,
        samplerate: int = TARGET_SAMPLE_RATE,
    ) -> None:
        if self._recording:
            return

        # stop monitoring to avoid opening a second stream on same device
        self.stop_monitor()

        with self._lock:
            self._chunks = []
            self._recording = True
            self._start_time = time.time()

        def _callback(indata, frames, time_info, status):  # noqa: ANN001
            if status:
                log.warning("Audio status: %s", status)
            mono = indata.mean(axis=1) if indata.ndim > 1 else indata
            mono = mono.astype(np.float32, copy=False)

            if mono.size:
                mono = mono - float(np.mean(mono))

            if mono.size:
                level = _rms(mono)
                with self._mon_lock:
                    self._mon_level = 0.7 * level + 0.3 * self._mon_level

            with self._lock:
                if self._recording:
                    self._chunks.append(mono.copy())

        try:
            self._stream = sd.InputStream(
                samplerate=samplerate,
                channels=TARGET_CHANNELS,
                dtype="float32",
                device=device_index,
                callback=_callback,
                blocksize=0,
                latency="low",
            )
            self._stream.start()
            log.info("Recording started (device=%s, sr=%d)", device_index, samplerate)
        except Exception as exc:
            with self._lock:
                self._recording = False
            log.exception("Failed to start recording")
            raise RuntimeError(f"خطا در شروع ضبط: {exc}") from exc

    def stop(self) -> RecordingResult | None:
        if not self._recording:
            return None
        with self._lock:
            self._recording = False

        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
        except Exception:
            log.exception("Error stopping stream")
        finally:
            self._stream = None

        with self._lock:
            chunks = self._chunks
            self._chunks = []

        # reset level after recording
        with self._mon_lock:
            self._mon_level = 0.0

        if not chunks:
            return None

        samples = np.concatenate(chunks).astype(np.float32, copy=False)
        duration = len(samples) / float(TARGET_SAMPLE_RATE)
        result = RecordingResult(
            samples=samples,
            sample_rate=TARGET_SAMPLE_RATE,
            duration=duration,
            started_at=self._start_time,
            stopped_at=time.time(),
        )
        log.info("Recording stopped: %.2fs", duration)
        return result

    def elapsed(self) -> float:
        if not self._recording:
            return 0.0
        return time.time() - self._start_time

    # ---------- monitoring ----------
    def start_monitor(
        self,
        device_index: int | None = None,
        samplerate: int = TARGET_SAMPLE_RATE,
    ) -> None:
        """Start a lightweight input stream used only for level metering."""
        if self._mon_stream is not None:
            return
        if self._recording:
            return

        def _callback(indata, frames, time_info, status):  # noqa: ANN001
            if status:
                log.debug("Monitor status: %s", status)
            mono = indata.mean(axis=1) if indata.ndim > 1 else indata
            level = _rms(mono)
            with self._mon_lock:
                self._mon_level = 0.7 * level + 0.3 * self._mon_level

        try:
            self._mon_stream = sd.InputStream(
                samplerate=samplerate,
                channels=TARGET_CHANNELS,
                dtype="float32",
                device=device_index,
                callback=_callback,
                blocksize=1024,
                latency="low",
            )
            self._mon_stream.start()
            log.info("Monitor started (device=%s)", device_index)
        except Exception as exc:
            self._mon_stream = None
            log.exception("Failed to start monitor")
            raise RuntimeError(f"خطا در شروع نمایشگر صدا: {exc}") from exc

    def stop_monitor(self) -> None:
        if self._mon_stream is None:
            return
        try:
            self._mon_stream.stop()
            self._mon_stream.close()
        except Exception:
            log.exception("Error stopping monitor stream")
        finally:
            self._mon_stream = None
            with self._mon_lock:
                self._mon_level = 0.0

    def current_level(self) -> float:
        with self._mon_lock:
            return self._mon_level

    def close(self) -> None:
        self.stop_monitor()
        if self._recording:
            self.stop()
