"""Enumerate microphone input devices."""

from __future__ import annotations

from dataclasses import dataclass

import sounddevice as sd


@dataclass(frozen=True)
class MicDevice:
    index: int
    name: str
    channels: int
    default_samplerate: float


def list_input_devices() -> list[MicDevice]:
    devices: list[MicDevice] = []
    try:
        raw = sd.query_devices()
    except Exception:
        return devices
    for idx, dev in enumerate(raw):
        if dev.get("max_input_channels", 0) > 0:
            devices.append(
                MicDevice(
                    index=idx,
                    name=str(dev.get("name", f"Device {idx}")),
                    channels=int(dev.get("max_input_channels", 1)),
                    default_samplerate=float(dev.get("default_samplerate", 16000)),
                )
            )
    return devices
