from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from lnkup.responder.controller import ResponderController
from .builder_view import BuilderView
from .responder_view import ResponderView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LNK-NG")
        self.resize(1080, 720)
        self.setMinimumSize(900, 620)

        self.controller = ResponderController(self)
        self.builder = BuilderView()
        self.responder = ResponderView(self.controller)
        self.responder.listener_selected.connect(self.builder.set_listener_host)

        self._build_ui()
        self._wire()

    def _build_ui(self) -> None:
        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top = QWidget()
        top.setObjectName("topBar")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(20, 12, 20, 12)

        brand = QLabel("LNK-NG")
        brand.setObjectName("brand")
        top_layout.addWidget(brand)
        top_layout.addSpacing(24)

        self.builder_button = QPushButton("LNK Builder")
        self.responder_button = QPushButton("Responder")
        for button in (self.builder_button, self.responder_button):
            button.setCheckable(True)
            button.setObjectName("navButton")
        self.builder_button.setChecked(True)
        nav = QButtonGroup(self)
        nav.setExclusive(True)
        nav.addButton(self.builder_button, 0)
        nav.addButton(self.responder_button, 1)
        self._nav = nav
        top_layout.addWidget(self.builder_button)
        top_layout.addWidget(self.responder_button)
        top_layout.addStretch(1)

        self.global_status = QLabel("RESPONDER · STOPPED")
        self.global_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(self.global_status)

        root.addWidget(top)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.builder)
        self.stack.addWidget(self.responder)
        root.addWidget(self.stack, 1)
        self.setCentralWidget(container)

    def _wire(self) -> None:
        self._nav.idClicked.connect(self.stack.setCurrentIndex)
        self.controller.state_changed.connect(self._global_state)

    def _global_state(self, state: str) -> None:
        self.global_status.setText(f"RESPONDER · {state.upper()}")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.controller.stop()
        super().closeEvent(event)
