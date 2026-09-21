"""A simple horizontal audio level meter widget (VU meter)."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget


class LevelMeter(QWidget):
    """Displays an RMS level (0.0 - 1.0) as a colored gradient bar."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._level: float = 0.0
        self._peak: float = 0.0
        self.setMinimumHeight(16)
        self.setMaximumHeight(18)
        self.setMinimumWidth(140)

    def set_level(self, rms: float) -> None:
        rms = max(0.0, min(1.0, float(rms)))
        if rms <= 1e-6:
            mapped = 0.0
        else:
            db = 20.0 * math.log10(rms)
            mapped = max(0.0, min(1.0, (db + 60.0) / 60.0))

        self._level = mapped
        if mapped > self._peak:
            self._peak = mapped
        else:
            self._peak = max(mapped, self._peak - 0.02)
        self.update()

    def reset(self) -> None:
        self._level = 0.0
        self._peak = 0.0
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(0, 0, -1, -1)
        radius = rect.height() / 2

        # پس‌زمینه (با کمی تیرگی)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1b1f27"))
        painter.drawRoundedRect(rect, radius, radius)

        # نوار سطح با گرادیان سبز→زرد→قرمز
        w = int(rect.width() * self._level)
        if w > 2:
            bar_rect = rect.adjusted(0, 0, -(rect.width() - w), 0)
            grad = QLinearGradient(bar_rect.left(), 0, rect.right(), 0)
            grad.setColorAt(0.0, QColor("#22c55e"))  # سبز
            grad.setColorAt(0.6, QColor("#eab308"))  # زرد
            grad.setColorAt(1.0, QColor("#ef4444"))  # قرمز
            painter.setBrush(grad)
            painter.drawRoundedRect(bar_rect, radius, radius)

        # نشانگر peak
        if self._peak > 0.01:
            px = int(rect.width() * self._peak) - 2
            px = max(0, min(px, rect.width() - 3))
            painter.setBrush(QColor("#e5e7eb"))
            painter.drawRect(px, 2, 2, rect.height() - 4)

        # قاب
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QColor("#2f3542"))
        painter.drawRoundedRect(rect, radius, radius)

        painter.end()
