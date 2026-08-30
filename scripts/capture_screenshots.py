from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from lnkup.app import STYLE
from lnkup.ui.main_window import MainWindow


def main() -> int:
    app = QApplication([])
    app.setStyleSheet(STYLE)
    out = Path("assets/screenshots")
    out.mkdir(parents=True, exist_ok=True)
    window = MainWindow()
    window.resize(1200, 780)
    window.show()
    app.processEvents()
    window.grab().save(str(out / "lnk-builder.png"))
    window.responder_button.click()
    app.processEvents()
    window.grab().save(str(out / "responder-workbench.png"))
    window.responder.tabs.setCurrentIndex(3)
    app.processEvents()
    window.grab().save(str(out / "protocol-details.png"))
    QTimer.singleShot(0, app.quit)
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
