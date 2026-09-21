"""Entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config.settings import load_settings
from app.ui.main_window import MainWindow
from app.utils.logger import setup_logging


def main() -> int:
    settings = load_settings()
    setup_logging(settings.log_level)

    app = QApplication(sys.argv)
    app.setApplicationName("Voice to Text")
    app.setOrganizationName("VoiceToText")

    # پشتیبانی خوب از RTL و فونت فارسی
    app.setLayoutDirection(app.layoutDirection())

    window = MainWindow(settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
