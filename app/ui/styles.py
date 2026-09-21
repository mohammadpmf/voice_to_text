"""Modern Light/Dark QSS stylesheets."""

from __future__ import annotations

_FONT_STACK = "'Vazirmatn', 'Segoe UI', 'Tahoma', sans-serif"


LIGHT_QSS = f"""
* {{ font-family: {_FONT_STACK}; font-size: 13px; }}

QMainWindow, QWidget#centralRoot {{
    background: #f6f7fb;
    color: #1f2430;
}}

QLabel {{
    color: #1f2430;
    background: transparent;
}}

/* ---------- Header ---------- */
QWidget#headerBar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4f46e5, stop:1 #9333ea);
    border-radius: 12px;
}}
QLabel#headerTitle {{
    color: #ffffff;
    font-size: 17px;
    font-weight: 600;
}}
QLabel#headerSubtitle {{
    color: #e5e7eb;
    font-size: 12px;
}}

/* ---------- Cards ---------- */
QFrame#card {{
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}}

/* ---------- Buttons ---------- */
QPushButton {{
    background: #eef1f6;
    border: 1px solid #d7dbe3;
    padding: 8px 14px;
    border-radius: 8px;
    color: #1f2430;
}}
QPushButton:hover {{ background: #e3e8f0; }}
QPushButton:pressed {{ background: #d7dde8; }}
QPushButton:disabled {{ color: #9099a8; background: #f1f3f7; }}

QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #6366f1, stop:1 #4f46e5);
    color: white;
    border: none;
    font-weight: 600;
    padding: 10px 20px;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #818cf8, stop:1 #6366f1);
}}
QPushButton#primary:disabled {{ background: #c7c9f5; color: #f0f0ff; }}

QPushButton#danger {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ef4444, stop:1 #dc2626);
    color: white;
    border: none;
    font-weight: 600;
    padding: 10px 20px;
}}
QPushButton#danger:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f87171, stop:1 #ef4444);
}}
QPushButton#danger:disabled {{ background: #f3b4b4; color: #fff; }}

/* ---------- Inputs ---------- */
QComboBox, QLineEdit {{
    background: #ffffff;
    border: 1px solid #d7dbe3;
    border-radius: 8px;
    padding: 6px 10px;
    color: #1f2430;
}}
QComboBox:hover, QLineEdit:hover {{ border-color: #a5b4fc; }}
QComboBox:focus, QLineEdit:focus {{ border-color: #6366f1; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: #ffffff;
    border: 1px solid #d7dbe3;
    selection-background-color: #e0e7ff;
    selection-color: #1f2430;
}}

QCheckBox {{ color: #374151; spacing: 6px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid #c7cdd8;
    border-radius: 4px;
    background: #ffffff;
}}
QCheckBox::indicator:checked {{
    background: #6366f1; border-color: #6366f1;
}}

/* ---------- Text editor ---------- */
QTextEdit {{
    background: #ffffff;
    color: #1f2430;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 14px;
    font-size: 15px;
    selection-background-color: #c7d2fe;
}}

/* ---------- Status ---------- */
QLabel#status {{ color: #4b5563; }}
QLabel#sectionTitle {{
    color: #6b7280;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLabel#recordingDot {{
    color: #dc2626;
    font-size: 16px;
    font-weight: 700;
}}

QStatusBar {{ background: #eef1f6; color: #4b5563; }}
QStatusBar::item {{ border: none; }}
"""


DARK_QSS = f"""
* {{ font-family: {_FONT_STACK}; font-size: 13px; }}

QMainWindow, QWidget#centralRoot {{
    background: #0f1116;
    color: #e6e9ef;
}}

QLabel {{
    color: #e6e9ef;
    background: transparent;
}}

/* ---------- Header ---------- */
QWidget#headerBar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4338ca, stop:1 #7e22ce);
    border-radius: 12px;
}}
QLabel#headerTitle {{
    color: #ffffff;
    font-size: 17px;
    font-weight: 600;
}}
QLabel#headerSubtitle {{
    color: #e9d5ff;
    font-size: 12px;
}}

/* ---------- Cards ---------- */
QFrame#card {{
    background: #171a21;
    border: 1px solid #262b34;
    border-radius: 12px;
}}

/* ---------- Buttons ---------- */
QPushButton {{
    background: #232833;
    border: 1px solid #2f3542;
    padding: 8px 14px;
    border-radius: 8px;
    color: #e6e9ef;
}}
QPushButton:hover {{ background: #2c3240; border-color: #3a4150; }}
QPushButton:pressed {{ background: #353c4b; }}
QPushButton:disabled {{ color: #6d7482; background: #1b1f27; }}

QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #6366f1, stop:1 #4f46e5);
    color: white;
    border: none;
    font-weight: 600;
    padding: 10px 20px;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #818cf8, stop:1 #6366f1);
}}
QPushButton#primary:disabled {{ background: #3b3f75; color: #c7c9e8; }}

QPushButton#danger {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ef4444, stop:1 #b91c1c);
    color: white;
    border: none;
    font-weight: 600;
    padding: 10px 20px;
}}
QPushButton#danger:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f87171, stop:1 #dc2626);
}}
QPushButton#danger:disabled {{ background: #5b2626; color: #f0c0c0; }}

/* ---------- Inputs ---------- */
QComboBox, QLineEdit {{
    background: #1b1f27;
    border: 1px solid #2f3542;
    border-radius: 8px;
    padding: 6px 10px;
    color: #e6e9ef;
}}
QComboBox:hover, QLineEdit:hover {{ border-color: #6366f1; }}
QComboBox:focus, QLineEdit:focus {{ border-color: #818cf8; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: #1b1f27;
    border: 1px solid #2f3542;
    color: #e6e9ef;
    selection-background-color: #4338ca;
    selection-color: #ffffff;
}}

QCheckBox {{ color: #cbd5e1; spacing: 6px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid #3a4150;
    border-radius: 4px;
    background: #1b1f27;
}}
QCheckBox::indicator:checked {{
    background: #6366f1; border-color: #6366f1;
}}

/* ---------- Text editor ---------- */
QTextEdit {{
    background: #141821;
    color: #e6e9ef;
    border: 1px solid #262b34;
    border-radius: 12px;
    padding: 14px;
    font-size: 15px;
    selection-background-color: #4338ca;
}}

/* ---------- Status ---------- */
QLabel#status {{ color: #a9b2c2; }}
QLabel#sectionTitle {{
    color: #7c8597;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLabel#recordingDot {{
    color: #ef4444;
    font-size: 16px;
    font-weight: 700;
}}

QStatusBar {{ background: #171a21; color: #a9b2c2; }}
QStatusBar::item {{ border: none; }}
"""
