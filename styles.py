"""Qt Style Sheet (QSS) applied to the whole application."""
STYLESHEET = """
QWidget { background: #bbdefb; color: #1f2937; font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; }
QLabel { background: transparent; }
QLabel#title { font-size: 20pt; font-weight: 700; color: #1b365d; }
QLabel#heading { font-size: 13pt; font-weight: 700; color: #1b365d; }
QLabel#error { color: #b91c1c; font-weight: 600; }
QLabel#hint, QLabel#cardLabel { color: #6b7280; }
QLabel#cardValue { font-size: 24pt; font-weight: 700; color: #1b365d; }
QFrame#card { background: white; border: 1px solid #dbe3ea; border-radius: 10px; }

QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit {
    background: white; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1px solid #1b365d; }

QPushButton { background: #1b365d; color: white; border: none; border-radius: 6px;
    padding: 8px 16px; font-weight: 600; }
QPushButton:hover { background: #132743; }
QPushButton:disabled { background: #cbd5e1; color: #94a3b8; }
QPushButton#danger { background: #dc2626; }
QPushButton#danger:hover { background: #b91c1c; }
QPushButton#danger:disabled { background: #cbd5e1; }

QTableWidget, QListWidget { background: white; alternate-background-color: #f1f5f9;
    border: 1px solid #dbe3ea; gridline-color: #e2e8f0;
    selection-background-color: #93c5fd; selection-color: #1b365d; }
QHeaderView::section { background: #1b365d; color: white; padding: 6px; border: none; font-weight: 600; }

QMenuBar { background: white; }
QMenuBar::item:selected, QMenu::item:selected { background: #dbeafe; color: #1b365d; }
QMenu { background: white; border: 1px solid #dbe3ea; }
QToolBar { background: #1b365d; border-bottom: 1px solid #132743; spacing: 6px; padding: 4px; }
QToolButton { background: transparent; color: white; padding: 6px 14px; border-radius: 6px; font-weight: 600; }
QToolButton:hover { background: #2c4d75; }
QStatusBar { background: white; color: #6b7280; }
"""
