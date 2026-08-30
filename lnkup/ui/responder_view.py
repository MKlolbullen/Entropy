from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Signal

from lnkup.core.interfaces import list_interfaces
from lnkup.responder.controller import ResponderController
from lnkup.responder.options import ResponderOptions
from lnkup.responder.preflight import run_preflight


class ResponderView(QWidget):
    listener_selected = Signal(str)

    def __init__(self, controller: ResponderController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._interfaces = []
        self._build_ui()
        self._wire()
        self.refresh_interfaces()
        self._run_preflight()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)
        title = QLabel("Responder")
        title.setObjectName("viewTitle")
        subtitle = QLabel("Preflight, configuration visibility, structured evidence, and one persistent Analyze-mode process.")
        subtitle.setObjectName("muted")
        root.addWidget(title)
        root.addWidget(subtitle)

        config = QGroupBox("Analysis configuration")
        form = QFormLayout(config)
        iface_row = QWidget()
        iface_layout = QHBoxLayout(iface_row)
        iface_layout.setContentsMargins(0, 0, 0, 0)
        self.interface = QComboBox()
        self.refresh = QPushButton("Refresh interfaces")
        self.refresh.clicked.connect(self.refresh_interfaces)
        iface_layout.addWidget(self.interface, 1)
        iface_layout.addWidget(self.refresh)
        form.addRow("Interface", iface_row)
        self.ip_label = QLabel("—")
        form.addRow("Listener IPv4", self.ip_label)
        self.executable = QLineEdit("responder")
        form.addRow("Executable", self.executable)

        options_row = QWidget()
        options_layout = QHBoxLayout(options_row)
        options_layout.setContentsMargins(0, 0, 0, 0)
        self.analyze = QCheckBox("Analyze only")
        self.analyze.setChecked(True)
        self.analyze.setEnabled(False)
        self.verbose = QCheckBox("Verbose")
        self.verbose.setChecked(True)
        self.quiet = QCheckBox("Quiet")
        options_layout.addWidget(self.analyze)
        options_layout.addWidget(self.verbose)
        options_layout.addWidget(self.quiet)
        options_layout.addStretch(1)
        form.addRow("Mode", options_row)
        self.command = QLineEdit()
        self.command.setReadOnly(True)
        form.addRow("Command preview", self.command)
        root.addWidget(config)

        controls = QHBoxLayout()
        self.status = QLabel("STOPPED")
        self.run_id = QLabel("No active session")
        self.run_id.setObjectName("muted")
        controls.addWidget(self.status)
        controls.addWidget(self.run_id)
        controls.addStretch(1)
        self.preflight_button = QPushButton("Run preflight")
        self.preflight_button.clicked.connect(self._run_preflight)
        self.start_button = QPushButton("Start analysis")
        self.start_button.setObjectName("primaryButton")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        controls.addWidget(self.preflight_button)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        root.addLayout(controls)

        tabs = QTabWidget()
        tabs.addTab(self._preflight_tab(), "Preflight")
        tabs.addTab(self._services_tab(), "Services")
        tabs.addTab(self._events_tab(), "Events")
        root.addWidget(tabs, 1)

    def _preflight_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.preflight_table = QTableWidget(0, 3)
        self.preflight_table.setHorizontalHeaderLabels(["Check", "Status", "Detail"])
        self.preflight_table.verticalHeader().setVisible(False)
        self.preflight_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.preflight_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.preflight_table)
        return page

    def _services_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        note = QLabel("Read-only view of service states discovered in Responder.conf. This screen does not modify the configuration.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.services_table = QTableWidget(0, 3)
        self.services_table.setHorizontalHeaderLabels(["Service", "Configured", "Section"])
        self.services_table.verticalHeader().setVisible(False)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.services_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.services_table)
        return page

    def _events_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Time", "Level", "Message"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        return page

    def _wire(self) -> None:
        self.interface.currentIndexChanged.connect(self._interface_changed)
        self.verbose.toggled.connect(self._update_preview)
        self.quiet.toggled.connect(self._update_preview)
        self.executable.textChanged.connect(self._update_preview)
        self.start_button.clicked.connect(self._start)
        self.stop_button.clicked.connect(self.controller.stop)
        self.controller.state_changed.connect(self._state_changed)
        self.controller.session_changed.connect(self._session_changed)
        self.controller.event_received.connect(self._add_event)
        self.controller.error.connect(lambda msg: QMessageBox.critical(self, "Responder", msg))

    def refresh_interfaces(self) -> None:
        current_name = self._selected_interface_name() if self.interface.count() else None
        self._interfaces = list_interfaces()
        self.interface.blockSignals(True)
        self.interface.clear()
        for iface in self._interfaces:
            label = iface.name + (f"  ({iface.ipv4})" if iface.ipv4 else "")
            self.interface.addItem(label, iface.name)
        self.interface.blockSignals(False)
        if current_name:
            for idx in range(self.interface.count()):
                if self.interface.itemData(idx) == current_name:
                    self.interface.setCurrentIndex(idx)
                    break
        self._interface_changed(self.interface.currentIndex())

    def _selected_interface_name(self) -> str:
        return self.interface.currentData() or self.interface.currentText().split()[0]

    def _interface_changed(self, index: int) -> None:
        if index < 0 or index >= len(self._interfaces):
            self.ip_label.setText("—")
            return
        iface = self._interfaces[index]
        self.ip_label.setText(iface.ipv4 or "No IPv4 address")
        if iface.ipv4:
            self.listener_selected.emit(iface.ipv4)
        self._update_preview()

    def _options(self) -> ResponderOptions:
        return ResponderOptions(
            interface=self._selected_interface_name(), analyze=True,
            verbose=self.verbose.isChecked(), quiet=self.quiet.isChecked(),
            executable=self.executable.text().strip() or "responder",
        )

    def _update_preview(self) -> None:
        if self.interface.count() == 0:
            self.command.setText("No interface selected")
            return
        try:
            self.command.setText(self.controller.command_preview(self._options()))
        except Exception as exc:
            self.command.setText(str(exc))

    def _run_preflight(self) -> None:
        report = run_preflight(self.executable.text().strip() or "responder")
        self.preflight_table.setRowCount(0)
        for check in report.checks:
            row = self.preflight_table.rowCount()
            self.preflight_table.insertRow(row)
            self.preflight_table.setItem(row, 0, QTableWidgetItem(check.name))
            self.preflight_table.setItem(row, 1, QTableWidgetItem(check.status))
            self.preflight_table.setItem(row, 2, QTableWidgetItem(check.detail))
        self.services_table.setRowCount(0)
        for service in report.services:
            row = self.services_table.rowCount()
            self.services_table.insertRow(row)
            state = "ON" if service.enabled is True else "OFF" if service.enabled is False else "UNKNOWN"
            self.services_table.setItem(row, 0, QTableWidgetItem(service.name))
            self.services_table.setItem(row, 1, QTableWidgetItem(state))
            self.services_table.setItem(row, 2, QTableWidgetItem(service.source))

    def _start(self) -> None:
        try:
            self.controller.start(self._options())
        except Exception as exc:
            QMessageBox.critical(self, "Unable to start Responder", str(exc))

    def _state_changed(self, state: str) -> None:
        self.status.setText(state.upper())
        running = state in {"starting", "running", "stopping"}
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(state in {"starting", "running"})
        self.interface.setEnabled(not running)
        self.executable.setEnabled(not running)

    def _session_changed(self, run_id: str) -> None:
        self.run_id.setText(f"Run {run_id}" if run_id else "No active session")

    def _add_event(self, timestamp: str, level: str, message: str) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.table.setItem(row, 1, QTableWidgetItem(level))
        self.table.setItem(row, 2, QTableWidgetItem(message))
        self.table.scrollToBottom()
