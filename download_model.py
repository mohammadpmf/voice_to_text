"""Download a Faster-Whisper model into ./models for offline use.

Usage:
    python download_model.py                # default: small
    python download_model.py medium
    python download_model.py large-v3
"""

from __future__ import annotations

import sys
from pathlib import Path

# مدل‌های پشتیبانی‌شده در Hugging Face (Systran)
MODEL_MAP = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large-v3": "Systran/faster-whisper-large-v3",
}

MODELS_DIR = Path(__file__).parent / "models"


def download(model_size: str) -> Path:
    if model_size not in MODEL_MAP:
        print(f"❌ مدل نامعتبر: {model_size}")
        print(f"مدل‌های مجاز: {', '.join(MODEL_MAP.keys())}")
        sys.exit(1)

    repo_id = MODEL_MAP[model_size]
    target = MODELS_DIR / f"faster-whisper-{model_size}"
    target.mkdir(parents=True, exist_ok=True)

    print(f"⬇️  دانلود مدل «{model_size}» از {repo_id}")
    print(f"📁 مقصد: {target}")
    print("   (این کار فقط یک بار انجام می‌شود؛ لطفاً صبر کنید…)\n")

    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(target),
        local_dir_use_symlinks=False,
        resume_download=True,
    )

    print(f"\n✅ دانلود کامل شد: {target}")
    print("   حالا برنامه بدون اینترنت هم کار می‌کند.")
    return target


def main() -> None:
    model_size = sys.argv[1] if len(sys.argv) > 1 else "small"
    download(model_size)


if __name__ == "__main__":
    main()
