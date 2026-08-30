from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from lnkup.app import STYLE
from lnkup.responder.events import parse_line
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
    for index, template in enumerate(window.responder._templates):
        if template.name == "Documentation lab":
            window.responder.template_select.setCurrentIndex(index)
            window.responder._load_template()
            break
    app.processEvents()
    window.grab().save(str(out / "responder-workbench.png"))

    window.responder.tabs.setCurrentIndex(3)
    event = parse_line("[LLMNR] request from 192.0.2.44 for name FILESERVER")
    if event:
        event.timestamp = "2026-08-30T00:00:00+00:00"
        event.scope = "IN"
        event.correlation_id = "corr-demo01"
        event.correlation_count = 3
        window.responder._add_event(event)
        window.responder.table.selectRow(0)
        window.responder.details.set_event(event.to_dict())
    app.processEvents()
    window.grab().save(str(out / "protocol-details.png"))

    QTimer.singleShot(0, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
