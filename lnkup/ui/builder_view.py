from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from lnkup.core.inspector import inspect_lnk
from lnkup.core.lnk import build_icon_location, generate_lnk
from lnkup.core.models import LnkSpec, PayloadType


class BuilderView(QWidget):
    listener_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)
        title = QLabel("LNK Builder")
        title.setObjectName("viewTitle")
        subtitle = QLabel("Build shortcuts or inspect existing Shell Link metadata in the same workspace.")
        subtitle.setObjectName("muted")
        root.addWidget(title)
        root.addWidget(subtitle)

        tabs = QTabWidget()
        tabs.addTab(self._build_tab(), "Build")
        tabs.addTab(self._inspect_tab(), "Inspect")
        root.addWidget(tabs, 1)

    def _build_tab(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        box = QGroupBox("Shortcut")
        form = QFormLayout(box)
        self.host = QLineEdit()
        self.host.setPlaceholderText("192.168.1.44")
        self.host.textChanged.connect(self.listener_changed)
        form.addRow("Listener host", self.host)

        payload_row = QWidget()
        payload_layout = QHBoxLayout(payload_row)
        payload_layout.setContentsMargins(0, 0, 0, 0)
        self.ntlm = QRadioButton("NTLM")
        self.environment = QRadioButton("Environment")
        self.ntlm.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.ntlm)
        group.addButton(self.environment)
        self._payload_group = group
        payload_layout.addWidget(self.ntlm)
        payload_layout.addWidget(self.environment)
        payload_layout.addStretch(1)
        form.addRow("Payload", payload_row)

        self.variables = QLineEdit("USERNAME COMPUTERNAME USERDOMAIN")
        self.variables.setEnabled(False)
        self.environment.toggled.connect(self.variables.setEnabled)
        form.addRow("Environment vars", self.variables)
        self.execute = QLineEdit(r"C:\Windows\explorer.exe .")
        form.addRow("Execute", self.execute)

        output_row = QWidget()
        output_layout = QHBoxLayout(output_row)
        output_layout.setContentsMargins(0, 0, 0, 0)
        self.output = QLineEdit(str(Path.cwd() / "out.lnk"))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        output_layout.addWidget(self.output, 1)
        output_layout.addWidget(browse)
        form.addRow("Output", output_row)
        root.addWidget(box)

        preview_box = QGroupBox("Preview")
        preview_layout = QFormLayout(preview_box)
        self.preview_type = QLabel("NTLM")
        self.preview_icon = QLabel("—")
        self.preview_args = QLabel("—")
        self.preview_args.setWordWrap(True)
        preview_layout.addRow("Type", self.preview_type)
        preview_layout.addRow("UNC icon", self.preview_icon)
        preview_layout.addRow("Arguments", self.preview_args)
        root.addWidget(preview_box)

        actions = QHBoxLayout()
        actions.addStretch(1)
        preview = QPushButton("Preview")
        preview.clicked.connect(self._preview)
        generate = QPushButton("Generate LNK")
        generate.setObjectName("primaryButton")
        generate.clicked.connect(self._generate)
        actions.addWidget(preview)
        actions.addWidget(generate)
        root.addLayout(actions)
        root.addStretch(1)
        return page

    def _inspect_tab(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        select = QGroupBox("Artifact")
        row = QHBoxLayout(select)
        self.inspect_path = QLineEdit()
        self.inspect_path.setPlaceholderText("Select an existing .lnk file")
        browse = QPushButton("Open…")
        browse.clicked.connect(self._browse_inspect)
        inspect = QPushButton("Inspect")
        inspect.setObjectName("primaryButton")
        inspect.clicked.connect(self._inspect)
        row.addWidget(self.inspect_path, 1)
        row.addWidget(browse)
        row.addWidget(inspect)
        root.addWidget(select)

        metadata = QGroupBox("Shell Link metadata")
        form = QFormLayout(metadata)
        self.inspect_valid = QLabel("—")
        self.inspect_parser = QLabel("—")
        self.inspect_target = QLabel("—")
        self.inspect_target.setWordWrap(True)
        self.inspect_args = QLabel("—")
        self.inspect_args.setWordWrap(True)
        self.inspect_workdir = QLabel("—")
        self.inspect_icon = QLabel("—")
        self.inspect_icon.setWordWrap(True)
        form.addRow("Header", self.inspect_valid)
        form.addRow("Parser", self.inspect_parser)
        form.addRow("Target", self.inspect_target)
        form.addRow("Arguments", self.inspect_args)
        form.addRow("Working directory", self.inspect_workdir)
        form.addRow("Icon", self.inspect_icon)
        root.addWidget(metadata)

        strings = QGroupBox("UNC references / extracted strings")
        strings_layout = QVBoxLayout(strings)
        self.inspect_strings = QPlainTextEdit()
        self.inspect_strings.setReadOnly(True)
        strings_layout.addWidget(self.inspect_strings)
        root.addWidget(strings, 1)
        return page

    def set_listener_host(self, host: str) -> None:
        if host and self.host.text() != host:
            self.host.setText(host)

    def _spec(self) -> LnkSpec:
        payload_type = PayloadType.ENVIRONMENT if self.environment.isChecked() else PayloadType.NTLM
        variables = [v.strip().strip("%") for v in self.variables.text().replace(",", " ").split() if v.strip()]
        return LnkSpec(
            host=self.host.text().strip(),
            output=Path(self.output.text()).expanduser(),
            payload_type=payload_type,
            environment_variables=variables,
            execute=self.execute.text(),
        )

    def _browse(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save LNK", self.output.text(), "Windows shortcut (*.lnk)")
        if path:
            self.output.setText(path if path.lower().endswith(".lnk") else path + ".lnk")

    def _browse_inspect(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Inspect LNK", "", "Windows shortcut (*.lnk);;All files (*)")
        if path:
            self.inspect_path.setText(path)
            self._inspect()

    def _preview(self) -> None:
        try:
            spec = self._spec()
            from lnkup.core.validation import validate_spec
            validate_spec(spec)
            self.preview_type.setText(spec.payload_type.value.upper())
            self.preview_icon.setText(build_icon_location(spec))
            self.preview_args.setText("/c " + spec.execute)
        except Exception as exc:
            QMessageBox.warning(self, "Invalid configuration", str(exc))

    def _generate(self) -> None:
        try:
            spec = self._spec()
            result = generate_lnk(spec)
            self.preview_type.setText(spec.payload_type.value.upper())
            self.preview_icon.setText(result.icon_location)
            self.preview_args.setText(result.arguments)
            QMessageBox.information(self, "LNK generated", f"Saved to:\n{result.output}")
        except Exception as exc:
            QMessageBox.critical(self, "Generation failed", str(exc))

    def _inspect(self) -> None:
        try:
            result = inspect_lnk(self.inspect_path.text())
            self.inspect_valid.setText("Valid Shell Link" if result.valid_header else "Invalid / unknown header")
            self.inspect_parser.setText(result.parser)
            self.inspect_target.setText(result.target_path or "—")
            self.inspect_args.setText(result.arguments or "—")
            self.inspect_workdir.setText(result.working_directory or "—")
            self.inspect_icon.setText(result.icon_location or "—")
            lines = []
            if result.unc_paths:
                lines.append("UNC REFERENCES")
                lines.extend(result.unc_paths)
                lines.append("")
            lines.append("EXTRACTED STRINGS")
            lines.extend(result.strings)
            self.inspect_strings.setPlainText("\n".join(lines))
        except Exception as exc:
            QMessageBox.critical(self, "Inspection failed", str(exc))
