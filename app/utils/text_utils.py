"""Persian text utilities."""

from __future__ import annotations

import re

# حروف عربی که در فارسی باید به معادل فارسی تبدیل شوند
_ARABIC_TO_PERSIAN = {
    "\u064a": "\u06cc",  # ي -> ی
    "\u0643": "\u06a9",  # ك -> ک
    "\u0629": "\u0647",  # ة -> ه
    "\u06c0": "\u0647",  # ۀ -> ه
}

_ZERO_WIDTH = "\u200c"


def normalize_persian(text: str) -> str:
    """Normalize common Persian typographic issues."""
    if not text:
        return text
    for src, dst in _ARABIC_TO_PERSIAN.items():
        text = text.replace(src, dst)
    # فاصله‌های تکراری
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def append_with_space(existing: str, new: str) -> str:
    """Append new text to existing with proper spacing."""
    new = normalize_persian(new)
    if not existing.strip():
        return new
    if not new:
        return existing
    sep = "" if existing.endswith((" ", "\n", _ZERO_WIDTH)) else " "
    return f"{existing}{sep}{new}"
