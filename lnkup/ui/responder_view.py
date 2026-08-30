from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from lnkup.core.attestation import export_attested_bundle, generate_signing_key, verify_attestation
from lnkup.core.evidence import export_bundle, list_runs, load_events
from lnkup.core.interfaces import list_interfaces
from lnkup.core.scope import EngagementScope, parse_network_text
from lnkup.core.templates import EngagementTemplate, list_templates, save_template
from lnkup.responder.controller import ResponderController
from lnkup.responder.options import ResponderOptions
from lnkup.responder.preflight import run_preflight
from .protocol_details import ProtocolDetailPane


class ResponderView(QWidget):
    listener_selected = Signal(str)

    def __init__(self, controller: ResponderController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._interfaces = []
        self._evidence_runs = []
        self._templates = []
        self._events_by_row: dict[int, dict] = {}
        self._build_ui()
        self._wire()
        self.refresh_interfaces()
        self._refresh_templates()
        self._run_preflight()
        self._refresh_evidence()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)
        title = QLabel("Responder")
        title.setObjectName("viewTitle")
        subtitle = QLabel("Analyze-mode telemetry with engagement templates, protocol details, and signed evidence.")
        subtitle.setObjectName("muted")
        root.addWidget(title)
        root.addWidget(subtitle)

        config = QGroupBox("Analysis configuration")
        form = QFormLayout(config)
        iface_row = QWidget()
        iface_layout = QHBoxLayout(iface_row)
        iface_layout.setContentsMargins(0, 0, 0, 0)
        self.interface = QComboBox()
        refresh = QPushButton("Refresh interfaces")
        refresh.clicked.connect(self.refresh_interfaces)
        iface_layout.addWidget(self.interface, 1)
        iface_layout.addWidget(refresh)
        form.addRow("Interface", iface_row)
        self.ip_label = QLabel("—")
        form.addRow("Listener IPv4", self.ip_label)
        self.executable = QLineEdit("responder")
        form.addRow("Executable", self.executable)
        mode = QWidget()
        mode_layout = QHBoxLayout(mode)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        locked = QCheckBox("Analyze only")
        locked.setChecked(True)
        locked.setEnabled(False)
        self.verbose = QCheckBox("Verbose")
        self.verbose.setChecked(True)
        self.quiet = QCheckBox("Quiet")
        mode_layout.addWidget(locked)
        mode_layout.addWidget(self.verbose)
        mode_layout.addWidget(self.quiet)
        mode_layout.addStretch(1)
        form.addRow("Mode", mode)
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
        self.start_button = QPushButton("Start analysis")
        self.start_button.setObjectName("primaryButton")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        controls.addWidget(self.preflight_button)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        root.addLayout(controls)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._engagement_tab(), "Engagement")
        self.tabs.addTab(self._preflight_tab(), "Preflight")
        self.tabs.addTab(self._services_tab(), "Services")
        self.tabs.addTab(self._events_tab(), "Events")
        self.tabs.addTab(self._evidence_tab(), "Evidence")
        root.addWidget(self.tabs, 1)

    def _engagement_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        template_row = QWidget()
        template_layout = QHBoxLayout(template_row)
        template_layout.setContentsMargins(0, 0, 0, 0)
        self.template_select = QComboBox()
        load = QPushButton("Load")
        save = QPushButton("Save current")
        load.clicked.connect(self._load_template)
        save.clicked.connect(self._save_template)
        template_layout.addWidget(self.template_select, 1)
        template_layout.addWidget(load)
        template_layout.addWidget(save)
        form.addRow("Template", template_row)
        self.engagement_name = QLineEdit("Unscoped analysis")
        self.scope_allow = QPlainTextEdit()
        self.scope_allow.setPlaceholderText("10.20.30.0/24\n192.0.2.0/28")
        self.scope_allow.setMaximumHeight(90)
        self.scope_exclude = QPlainTextEdit()
        self.scope_exclude.setPlaceholderText("10.20.30.1/32")
        self.scope_exclude.setMaximumHeight(70)
        self.scope_status = QLabel("No allowlist configured: observed sources are tagged UNKNOWN.")
        self.scope_status.setWordWrap(True)
        self.scope_status.setObjectName("muted")
        validate = QPushButton("Validate scope")
        validate.clicked.connect(self._validate_scope)
        form.addRow("Engagement", self.engagement_name)
        form.addRow("Allowed CIDRs", self.scope_allow)
        form.addRow("Excluded CIDRs", self.scope_exclude)
        form.addRow("", validate)
        form.addRow("Status", self.scope_status)
        return page

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
        note = QLabel("Read-only Responder.conf service state. LNK-NG never mutates the configuration.")
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
        filters = QHBoxLayout()
        self.protocol_filter = QComboBox()
        self.protocol_filter.addItem("All protocols")
        self.scope_filter = QComboBox()
        self.scope_filter.addItems(["All scopes", "IN", "OUT", "UNKNOWN"])
        self.event_search = QLineEdit()
        self.event_search.setPlaceholderText("Filter events…")
        filters.addWidget(self.protocol_filter)
        filters.addWidget(self.scope_filter)
        filters.addWidget(self.event_search, 1)
        layout.addLayout(filters)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Time", "Protocol", "Type", "Source", "Scope", "Corr.", "Message"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        for column in range(6):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.details = ProtocolDetailPane()
        splitter.addWidget(self.table)
        splitter.addWidget(self.details)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)
        return page

    def _evidence_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        toolbar = QHBoxLayout()
        self.evidence_select = QComboBox()
        refresh = QPushButton("Refresh")
        export = QPushButton("Export ZIP")
        attest = QPushButton("Attest + export")
        keygen = QPushButton("New signing key")
        verify = QPushButton("Verify attestation")
        refresh.clicked.connect(self._refresh_evidence)
        export.clicked.connect(self._export_evidence)
        attest.clicked.connect(self._export_attested)
        keygen.clicked.connect(self._generate_key)
        verify.clicked.connect(self._verify_attestation)
        self.evidence_select.currentIndexChanged.connect(self._load_evidence)
        toolbar.addWidget(self.evidence_select, 1)
        for button in (refresh, export, attest, keygen, verify):
            toolbar.addWidget(button)
        layout.addLayout(toolbar)
        self.evidence_summary = QLabel("No stored runs")
        self.evidence_summary.setObjectName("muted")
        self.evidence_summary.setWordWrap(True)
        layout.addWidget(self.evidence_summary)
        self.evidence_table = QTableWidget(0, 7)
        self.evidence_table.setHorizontalHeaderLabels(["Time", "Protocol", "Type", "Source", "Scope", "Corr.", "Message"])
        self.evidence_table.verticalHeader().setVisible(False)
        self.evidence_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.evidence_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.evidence_table, 1)
        return page

    def _wire(self) -> None:
        self.interface.currentIndexChanged.connect(self._interface_changed)
        self.verbose.toggled.connect(self._update_preview)
        self.quiet.toggled.connect(self._update_preview)
        self.executable.textChanged.connect(self._update_preview)
        self.preflight_button.clicked.connect(self._run_preflight)
        self.start_button.clicked.connect(self._start)
        self.stop_button.clicked.connect(self.controller.stop)
        self.controller.state_changed.connect(self._state_changed)
        self.controller.session_changed.connect(self._session_changed)
        self.controller.event_received.connect(self._add_event)
        self.controller.error.connect(lambda msg: QMessageBox.critical(self, "Responder", msg))
        self.protocol_filter.currentTextChanged.connect(self._apply_event_filters)
        self.scope_filter.currentTextChanged.connect(self._apply_event_filters)
        self.event_search.textChanged.connect(self._apply_event_filters)
        self.table.itemSelectionChanged.connect(self._show_selected_event)

    def refresh_interfaces(self) -> None:
        current = self._selected_interface_name() if self.interface.count() else None
        self._interfaces = list_interfaces()
        self.interface.blockSignals(True)
        self.interface.clear()
        for iface in self._interfaces:
            self.interface.addItem(iface.name + (f"  ({iface.ipv4})" if iface.ipv4 else ""), iface.name)
        self.interface.blockSignals(False)
        if current:
            for index in range(self.interface.count()):
                if self.interface.itemData(index) == current:
                    self.interface.setCurrentIndex(index)
                    break
        self._interface_changed(self.interface.currentIndex())

    def _selected_interface_name(self) -> str:
        return self.interface.currentData() or (self.interface.currentText().split()[0] if self.interface.currentText() else "")

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
        return ResponderOptions(interface=self._selected_interface_name(), analyze=True, verbose=self.verbose.isChecked(), quiet=self.quiet.isChecked(), executable=self.executable.text().strip() or "responder")

    def _scope(self) -> EngagementScope:
        return EngagementScope(name=self.engagement_name.text(), allowed_cidrs=parse_network_text(self.scope_allow.toPlainText()), excluded_cidrs=parse_network_text(self.scope_exclude.toPlainText()))

    def _refresh_templates(self) -> None:
        self._templates = list_templates()
        self.template_select.clear()
        for template in self._templates:
            self.template_select.addItem(template.name)

    def _load_template(self) -> None:
        index = self.template_select.currentIndex()
        if index < 0:
            return
        template = self._templates[index]
        self.engagement_name.setText(template.name)
        self.scope_allow.setPlainText("\n".join(template.allowed_cidrs))
        self.scope_exclude.setPlainText("\n".join(template.excluded_cidrs))
        self.scope_status.setText(template.description)

    def _save_template(self) -> None:
        try:
            scope = self._scope()
            path = save_template(EngagementTemplate(scope.name, "User-saved engagement template.", scope.allowed_cidrs, scope.excluded_cidrs))
            self._refresh_templates()
            QMessageBox.information(self, "Template saved", str(path))
        except Exception as exc:
            QMessageBox.critical(self, "Template", str(exc))

    def _validate_scope(self) -> None:
        try:
            scope = self._scope()
            detail = f"{len(scope.allowed_cidrs)} allowed network(s), {len(scope.excluded_cidrs)} exclusion(s)."
            if not scope.allowed_cidrs:
                detail += " Sources remain UNKNOWN without an allowlist."
            self.scope_status.setText(detail)
        except ValueError as exc:
            self.scope_status.setText(f"Invalid scope: {exc}")

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
            for column, value in enumerate((check.name, check.status, check.detail)):
                self.preflight_table.setItem(row, column, QTableWidgetItem(value))
        self.services_table.setRowCount(0)
        for service in report.services:
            row = self.services_table.rowCount()
            self.services_table.insertRow(row)
            state = "ON" if service.enabled is True else "OFF" if service.enabled is False else "UNKNOWN"
            for column, value in enumerate((service.name, state, service.source)):
                self.services_table.setItem(row, column, QTableWidgetItem(value))

    def _start(self) -> None:
        try:
            self.controller.set_scope(self._scope())
            self.controller.start(self._options())
        except Exception as exc:
            QMessageBox.critical(self, "Unable to start Responder", str(exc))

    def _state_changed(self, state: str) -> None:
        self.status.setText(state.upper())
        running = state in {"starting", "running", "stopping"}
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(state in {"starting", "running"})
        for widget in (self.interface, self.executable, self.engagement_name, self.scope_allow, self.scope_exclude, self.template_select):
            widget.setEnabled(not running)

    def _session_changed(self, run_id: str) -> None:
        self.run_id.setText(f"Run {run_id}" if run_id else "No active session")
        if not run_id:
            self._refresh_evidence()

    def _add_event(self, event) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        event_data = event.to_dict()
        self._events_by_row[row] = event_data
        values = (event.timestamp, event.protocol, event.event_type, event.source or "—", event.scope, event.correlation_id or "—", event.message)
        for column, value in enumerate(values):
            self.table.setItem(row, column, QTableWidgetItem(str(value)))
        if self.protocol_filter.findText(event.protocol) < 0:
            self.protocol_filter.addItem(event.protocol)
        self._apply_event_filters()
        self.table.scrollToBottom()

    def _show_selected_event(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            event = self._events_by_row.get(rows[0].row())
            if event:
                self.details.set_event(event)

    def _apply_event_filters(self) -> None:
        protocol = self.protocol_filter.currentText()
        scope = self.scope_filter.currentText()
        needle = self.event_search.text().lower().strip()
        for row in range(self.table.rowCount()):
            row_protocol = self.table.item(row, 1).text()
            row_scope = self.table.item(row, 4).text()
            haystack = " ".join(self.table.item(row, column).text() for column in range(self.table.columnCount())).lower()
            visible = (protocol == "All protocols" or protocol == row_protocol) and (scope == "All scopes" or scope == row_scope) and (not needle or needle in haystack)
            self.table.setRowHidden(row, not visible)

    def _refresh_evidence(self) -> None:
        self._evidence_runs = list_runs(self.controller.runs.root)
        self.evidence_select.blockSignals(True)
        self.evidence_select.clear()
        for run in self._evidence_runs:
            name = run.manifest.get("metadata", {}).get("engagement", {}).get("name", "Unscoped analysis")
            self.evidence_select.addItem(f"{run.run_id} · {name} · {run.event_count} · {run.integrity}")
        self.evidence_select.blockSignals(False)
        self._load_evidence(self.evidence_select.currentIndex())

    def _load_evidence(self, index: int) -> None:
        self.evidence_table.setRowCount(0)
        if index < 0 or index >= len(self._evidence_runs):
            self.evidence_summary.setText("No stored runs")
            return
        run = self._evidence_runs[index]
        engagement = run.manifest.get("metadata", {}).get("engagement", {})
        attested, _ = verify_attestation(run.directory)
        self.evidence_summary.setText(f"{run.run_id} · {engagement.get('name', 'Unscoped analysis')} · {run.event_count} event(s) · integrity {run.integrity} · attestation {'VERIFIED' if attested else 'none/unverified'}")
        for event in load_events(run):
            row = self.evidence_table.rowCount()
            self.evidence_table.insertRow(row)
            values = (event.get("timestamp", ""), event.get("protocol", "SYSTEM"), event.get("event_type", "log"), event.get("source") or "—", event.get("scope", "UNKNOWN"), event.get("correlation_id") or "—", event.get("message", ""))
            for column, value in enumerate(values):
                self.evidence_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _selected_run(self):
        index = self.evidence_select.currentIndex()
        return self._evidence_runs[index] if 0 <= index < len(self._evidence_runs) else None

    def _export_evidence(self) -> None:
        run = self._selected_run()
        if not run:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export evidence", f"{run.run_id}.zip", "ZIP archive (*.zip)")
        if path:
            QMessageBox.information(self, "Evidence exported", str(export_bundle(run, path)))

    def _generate_key(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Create Ed25519 signing key", "lnk-ng-signing.pem", "PEM key (*.pem)")
        if path:
            private, public = generate_signing_key(path)
            QMessageBox.information(self, "Signing key created", f"Private: {private}\nPublic: {public}\n\nKeep the private key outside evidence bundles.")

    def _export_attested(self) -> None:
        run = self._selected_run()
        if not run:
            return
        key, _ = QFileDialog.getOpenFileName(self, "Select Ed25519 private key", "", "PEM key (*.pem);;All files (*)")
        if not key:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export attested evidence", f"{run.run_id}-attested.zip", "ZIP archive (*.zip)")
        if path:
            try:
                result = export_attested_bundle(run.directory, key, path)
                self._refresh_evidence()
                QMessageBox.information(self, "Attested evidence exported", str(result))
            except Exception as exc:
                QMessageBox.critical(self, "Attestation failed", str(exc))

    def _verify_attestation(self) -> None:
        run = self._selected_run()
        if not run:
            return
        ok, detail = verify_attestation(run.directory)
        QMessageBox.information(self, "Attestation verification", f"{'VERIFIED' if ok else 'FAILED'}\n{detail}")
