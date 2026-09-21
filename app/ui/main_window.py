"""Main application window (PySide6) - Local Whisper only."""

from __future__ import annotations

from PySide6.QtCore import (
    QObject,
    QRunnable,
    QThread,
    QThreadPool,
    QTimer,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.audio.devices import list_input_devices
from app.audio.recorder import AudioRecorder, RecordingResult
from app.config.settings import Settings
from app.providers import create_provider
from app.providers.local_whisper import MODEL_SIZES
from app.speech.base import SpeechToTextProvider
from app.ui.level_meter import LevelMeter
from app.ui.styles import DARK_QSS, LIGHT_QSS
from app.utils.logger import get_logger
from app.utils.text_utils import append_with_space

log = get_logger(__name__)


# ---------------- Worker: transcription ----------------
class TranscribeWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, provider, audio, sample_rate, language):
        super().__init__()
        self._provider = provider
        self._audio = audio
        self._sample_rate = sample_rate
        self._language = language

    @Slot()
    def run(self) -> None:
        try:
            result = self._provider.transcribe(
                self._audio,
                sample_rate=self._sample_rate,
                language=self._language,
                progress_cb=lambda msg: self.progress.emit(msg),
            )
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            log.exception("Transcription failed")
            self.failed.emit(str(exc))


class _Runnable(QRunnable):
    def __init__(self, fn, on_done=None, on_error=None):
        super().__init__()
        self._fn = fn
        self._on_done = on_done
        self._on_error = on_error

    @Slot()
    def run(self) -> None:
        try:
            result = self._fn()
            if self._on_done:
                self._on_done(result)
        except Exception as exc:  # noqa: BLE001
            log.exception("Background task failed")
            if self._on_error:
                self._on_error(str(exc))


# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    _sig_monitor_started = Signal()
    _sig_monitor_failed = Signal(str)
    _sig_recording_started = Signal()
    _sig_recording_error = Signal(str)
    _sig_stopped = Signal(object)
    _sig_stopped_error = Signal(str)

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.recorder = AudioRecorder()
        self.provider: SpeechToTextProvider | None = None
        self._thread: QThread | None = None
        self._worker: TranscribeWorker | None = None
        self._pool = QThreadPool.globalInstance()

        self._is_processing: bool = False

        self.setWindowTitle("Voice to Text")
        self.resize(960, 700)
        self.setMinimumSize(820, 600)

        self._build_ui()
        self._populate_devices()
        self._populate_models()
        self._apply_theme()  # dark by default
        self._setup_shortcuts()

        # level meter timer
        self._level_timer = QTimer(self)
        self._level_timer.setInterval(50)
        self._level_timer.timeout.connect(self._update_level)

        # recording dot blink timer
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(600)
        self._blink_timer.timeout.connect(self._blink_dot)
        self._blink_on = True

        # signals (all handled on UI thread)
        self._sig_monitor_started.connect(self._on_monitor_started)
        self._sig_monitor_failed.connect(self._on_monitor_failed)
        self._sig_recording_started.connect(self._on_recording_started)
        self._sig_recording_error.connect(self._on_recording_error)
        self._sig_stopped.connect(self._on_stopped)
        self._sig_stopped_error.connect(self._on_stopped_error)

        # initial provider (Local)
        try:
            self.provider = create_provider("local", self.settings)
        except Exception as exc:  # noqa: BLE001
            log.exception("Provider init failed")
            self._set_status(f"خطای راه‌اندازی Provider: {exc}")

        QTimer.singleShot(200, self._start_monitor_on_current_device)

    # ---------- UI ----------
    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ===== Header =====
        header = QWidget()
        header.setObjectName("headerBar")
        header.setFixedHeight(64)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 8, 18, 8)
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        t1 = QLabel("🎙️  Voice to Text")
        t1.setObjectName("headerTitle")
        t2 = QLabel("تبدیل گفتار فارسی به متن — کاملاً آفلاین")
        t2.setObjectName("headerSubtitle")
        title_box.addWidget(t1)
        title_box.addWidget(t2)
        hl.addLayout(title_box)
        hl.addStretch(1)
        self.dark_check = QCheckBox("حالت تاریک")
        self.dark_check.setChecked(True)
        hl.addWidget(self.dark_check)
        root.addWidget(header)

        # ===== Card: settings =====
        settings_card = QFrame()
        settings_card.setObjectName("card")
        sc = QHBoxLayout(settings_card)
        sc.setContentsMargins(16, 12, 16, 12)
        sc.setSpacing(14)

        def _labeled(label_text: str, widget: QWidget) -> QWidget:
            box = QVBoxLayout()
            box.setSpacing(2)
            lbl = QLabel(label_text)
            lbl.setObjectName("sectionTitle")
            box.addWidget(lbl)
            box.addWidget(widget)
            w = QWidget()
            w.setLayout(box)
            return w

        self.mic_combo = QComboBox()
        self.mic_combo.setMinimumWidth(260)
        sc.addWidget(_labeled("میکروفون", self.mic_combo), 3)

        self.model_combo = QComboBox()
        self.model_combo.addItems(MODEL_SIZES)
        sc.addWidget(_labeled("مدل Whisper", self.model_combo), 2)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["fa", "en", "auto"])
        sc.addWidget(_labeled("زبان", self.lang_combo), 1)

        root.addWidget(settings_card)

        # ===== Card: level meter =====
        level_card = QFrame()
        level_card.setObjectName("card")
        lc = QHBoxLayout(level_card)
        lc.setContentsMargins(16, 10, 16, 10)
        lc.setSpacing(12)

        self.level_title = QLabel("🎚️  سطح صدا:")
        self.level_title.setObjectName("status")
        lc.addWidget(self.level_title)

        self.level_meter = LevelMeter()
        self.level_meter.setMinimumWidth(300)
        self.level_meter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lc.addWidget(self.level_meter, 1)

        self.level_hint = QLabel("⏳ در حال آماده‌سازی…")
        self.level_hint.setMinimumWidth(140)
        self.level_hint.setObjectName("status")
        lc.addWidget(self.level_hint)
        root.addWidget(level_card)

        # ===== Editor =====
        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "متن تبدیل‌شده اینجا نمایش داده می‌شود…\n"
            "برای شروع، دکمه‌ی «شروع ضبط» را بزنید یا از Ctrl+Shift+Space استفاده کنید."
        )
        self.editor.setAcceptRichText(False)
        self.editor.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root.addWidget(self.editor, 1)

        # ===== Status row =====
        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        self.recording_dot = QLabel("")
        self.recording_dot.setObjectName("recordingDot")
        self.recording_dot.setFixedWidth(18)
        status_row.addWidget(self.recording_dot)

        self.status_label = QLabel("آماده")
        self.status_label.setObjectName("status")
        status_row.addWidget(self.status_label, 1)
        root.addLayout(status_row)

        # ===== Buttons =====
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        self.start_btn = QPushButton("⏺  شروع ضبط")
        self.start_btn.setObjectName("primary")
        self.stop_btn = QPushButton("⏹  توقف")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.clear_btn = QPushButton("🗑  پاک کردن")
        self.copy_btn = QPushButton("📋  کپی همه")
        self.save_btn = QPushButton("💾  ذخیره TXT")
        self.append_check = QCheckBox("افزودن به متن قبلی")
        self.append_check.setChecked(True)

        for b in (self.start_btn, self.stop_btn):
            b.setMinimumHeight(40)
            b.setMinimumWidth(140)
            buttons.addWidget(b)
        buttons.addSpacing(8)
        for b in (self.clear_btn, self.copy_btn, self.save_btn):
            b.setMinimumHeight(36)
            buttons.addWidget(b)
        buttons.addStretch(1)
        buttons.addWidget(self.append_check)
        root.addLayout(buttons)

        # ===== Signals =====
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.clear_btn.clicked.connect(self.editor.clear)
        self.copy_btn.clicked.connect(self.copy_all)
        self.save_btn.clicked.connect(self.save_text)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        self.dark_check.toggled.connect(self._on_theme_toggled)
        self.mic_combo.currentIndexChanged.connect(self._on_mic_changed)

        self.statusBar().showMessage("آماده")

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Shift+Space"), self).activated.connect(
            self._toggle_recording
        )
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_text)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self.editor.clear)

    # ---------- populate ----------
    def _populate_devices(self) -> None:
        self.mic_combo.blockSignals(True)
        self.mic_combo.clear()
        self.mic_combo.addItem("پیش‌فرض سیستم", userData=None)
        for dev in list_input_devices():
            self.mic_combo.addItem(f"[{dev.index}] {dev.name}", userData=dev.index)
        self.mic_combo.blockSignals(False)

    def _populate_models(self) -> None:
        for combo, value in (
            (self.model_combo, self.settings.whisper_model),
            (self.lang_combo, self.settings.whisper_language),
        ):
            idx = combo.findText(value)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    # ---------- mic / monitor ----------
    def _current_mic_index(self) -> int | None:
        data = self.mic_combo.currentData()
        return data if isinstance(data, int) else None

    def _start_monitor_on_current_device(self) -> None:
        device_index = self._current_mic_index()
        self.level_hint.setText("⏳ در حال آماده‌سازی…")
        self.level_meter.reset()

        def _work():
            try:
                self.recorder.stop_monitor()
            except Exception:
                log.exception("stop_monitor failed")
            self.recorder.start_monitor(device_index=device_index)

        def _done(_):
            self._sig_monitor_started.emit()

        def _err(msg: str):
            self._sig_monitor_failed.emit(msg)

        self._pool.start(_Runnable(_work, on_done=_done, on_error=_err))

    @Slot()
    def _on_monitor_started(self) -> None:
        self._level_timer.start()
        self._set_status("نمایشگر صدا فعال است — صحبت کنید تا نوار حرکت کند.")

    @Slot(str)
    def _on_monitor_failed(self, msg: str) -> None:
        self._level_timer.stop()
        self.level_meter.reset()
        self.level_hint.setText("⚠️ خطا")
        self._set_status(f"خطا در فعال‌سازی میکروفون: {msg}")

    def _on_mic_changed(self, _index: int) -> None:
        if self.recorder.is_recording or self._is_processing:
            return
        self._start_monitor_on_current_device()

    @Slot()
    def _update_level(self) -> None:
        level = self.recorder.current_level()
        self.level_meter.set_level(level)

        if self.recorder.is_recording:
            self.level_hint.setText("⏺ در حال ضبط")
        elif self._is_processing:
            self.level_hint.setText("⏳ در حال پردازش")
        else:
            if level < 0.02:
                self.level_hint.setText("🔇 سکوت")
            elif level < 0.15:
                self.level_hint.setText("🔈 ضعیف")
            elif level < 0.5:
                self.level_hint.setText("🔉 خوب")
            else:
                self.level_hint.setText("🔊 بلند")

    # ---------- events ----------
    def _on_model_changed(self, name: str) -> None:
        self.settings.whisper_model = name

    def _on_theme_toggled(self, dark: bool) -> None:
        self._apply_theme(dark)

    def _apply_theme(self, dark: bool = True) -> None:
        self.setStyleSheet(DARK_QSS if dark else LIGHT_QSS)

    # ---------- recording ----------
    @Slot()
    def _toggle_recording(self) -> None:
        if self.recorder.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    @Slot()
    def start_recording(self) -> None:
        if self.recorder.is_recording or self._is_processing:
            return
        device_index = self._current_mic_index()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self._set_status("⏳ در حال آماده‌سازی میکروفون…")

        def _work():
            self.recorder.start(device_index=device_index)

        def _done(_):
            self._sig_recording_started.emit()

        def _err(msg: str):
            self._sig_recording_error.emit(msg)

        self._pool.start(_Runnable(_work, on_done=_done, on_error=_err))

    @Slot()
    def _on_recording_started(self) -> None:
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._set_status("🔴 در حال ضبط…")
        self.recording_dot.setText("●")
        self._blink_on = True
        self._blink_timer.start()

    @Slot(str)
    def _on_recording_error(self, msg: str) -> None:
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.critical(self, "خطای میکروفون", msg)
        self._set_status("خطا در شروع ضبط")
        self._start_monitor_on_current_device()

    @Slot()
    def stop_recording(self) -> None:
        if not self.recorder.is_recording:
            return

        self._is_processing = True
        self._blink_timer.stop()
        self.recording_dot.setText("●")
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self._set_status("⏳ در حال بستن میکروفون…")

        def _work():
            return self.recorder.stop()

        def _done(result):
            self._sig_stopped.emit(result)

        def _err(msg: str):
            self._sig_stopped_error.emit(msg)

        self._pool.start(_Runnable(_work, on_done=_done, on_error=_err))

    @Slot(object)
    def _on_stopped(self, result: RecordingResult | None) -> None:
        if result is None or len(result.samples) == 0:
            self._is_processing = False
            self.recording_dot.setText("")
            self._set_status("صدایی ضبط نشد.")
            self.start_btn.setEnabled(True)
            self._start_monitor_on_current_device()
            return
        self._set_status(f"در حال پردازش ({result.duration:.1f} ثانیه)…")
        self._start_monitor_on_current_device()
        self._start_transcription(result)

    @Slot(str)
    def _on_stopped_error(self, msg: str) -> None:
        self._is_processing = False
        self.recording_dot.setText("")
        self._set_status(f"خطا در توقف ضبط: {msg}")
        self.start_btn.setEnabled(True)

    def _start_transcription(self, result: RecordingResult) -> None:
        if self.provider is None:
            try:
                self.provider = create_provider("local", self.settings)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "خطای Provider", str(exc))
                self._reset_buttons()
                return

        self.settings.whisper_model = self.model_combo.currentText()
        language = self.lang_combo.currentText()

        self._thread = QThread(self)
        self._worker = TranscribeWorker(
            self.provider, result.samples, result.sample_rate, language
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._set_status)
        self._worker.finished.connect(self._on_transcription_done)
        self._worker.failed.connect(self._on_transcription_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    @Slot(object)
    def _on_transcription_done(self, result) -> None:
        text = result.text or ""
        if self.append_check.isChecked():
            merged = append_with_space(self.editor.toPlainText(), text)
            self.editor.setPlainText(merged)
        else:
            self.editor.setPlainText(text)

        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.editor.setTextCursor(cursor)

        self._set_status(f"✅ تمام شد ({result.provider}).")
        self._reset_buttons()

    @Slot(str)
    def _on_transcription_failed(self, message: str) -> None:
        QMessageBox.critical(self, "خطای تبدیل", message)
        self._set_status("خطا در تبدیل صدا به متن")
        self._reset_buttons()

    def _reset_buttons(self) -> None:
        self._is_processing = False
        self.recording_dot.setText("")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._worker = None
        self._thread = None

    # ---------- helpers ----------
    def _blink_dot(self) -> None:
        self._blink_on = not self._blink_on
        self.recording_dot.setText("●" if self._blink_on else " ")

    def _set_status(self, msg: str) -> None:
        self.status_label.setText(msg)
        self.statusBar().showMessage(msg, 4000)

    @Slot()
    def copy_all(self) -> None:
        QApplication.clipboard().setText(self.editor.toPlainText())
        self._set_status("متن در Clipboard کپی شد.")

    @Slot()
    def save_text(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره متن", "transcript.txt", "Text Files (*.txt)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self._set_status(f"ذخیره شد: {path}")
        except OSError as exc:
            QMessageBox.critical(self, "خطای ذخیره", str(exc))

    # ---------- lifecycle ----------
    def closeEvent(self, event) -> None:  # noqa: N802
        try:
            self._level_timer.stop()
            self._blink_timer.stop()
            self._pool.start(_Runnable(self.recorder.close))
            if self.provider is not None:
                self.provider.close()
        except Exception:
            log.exception("Cleanup error")
        super().closeEvent(event)
