from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from lnkup.ui import MainWindow


STYLE = """
QWidget {
    background: #0f1117;
    color: #e8eaf0;
    font-size: 13px;
}
#topBar {
    background: #171a23;
    border-bottom: 1px solid #292d3b;
}
#brand {
    font-size: 20px;
    font-weight: 700;
}
#viewTitle {
    font-size: 24px;
    font-weight: 700;
}
#muted {
    color: #969db0;
}
QGroupBox {
    border: 1px solid #2b3040;
    border-radius: 9px;
    margin-top: 12px;
    padding: 14px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
}
QLineEdit, QComboBox, QTableWidget {
    background: #151924;
    border: 1px solid #30364a;
    border-radius: 6px;
    padding: 7px;
}
QPushButton {
    background: #202635;
    border: 1px solid #343b50;
    border-radius: 6px;
    padding: 7px 12px;
}
QPushButton:hover {
    background: #293043;
}
QPushButton:checked, #primaryButton {
    background: #216869;
    border-color: #2e8586;
}
QPushButton:disabled {
    color: #666c7a;
    background: #181b23;
}
#navButton {
    min-width: 110px;
}
QHeaderView::section {
    background: #191d28;
    padding: 7px;
    border: 0;
    border-bottom: 1px solid #30364a;
}
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("LNK-NG")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
