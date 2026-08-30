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
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

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
        root.setSpacing(16)

        title = QLabel("LNK Builder")
        title.setObjectName("viewTitle")
        subtitle = QLabel("Build and inspect the shortcut configuration before writing it to disk.")
        subtitle.setObjectName("muted")
        root.addWidget(title)
        root.addWidget(subtitle)

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
        self.variables.setPlaceholderText("USERNAME COMPUTERNAME USERDOMAIN")
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
        inspect = QPushButton("Preview")
        inspect.clicked.connect(self._preview)
        generate = QPushButton("Generate LNK")
        generate.setObjectName("primaryButton")
        generate.clicked.connect(self._generate)
        actions.addWidget(inspect)
        actions.addWidget(generate)
        root.addLayout(actions)
        root.addStretch(1)

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
            if not path.lower().endswith(".lnk"):
                path += ".lnk"
            self.output.setText(path)

    def _preview(self) -> None:
        try:
            spec = self._spec()
            from lnkup.core.validation import validate_spec

            validate_spec(spec)
            icon = build_icon_location(spec)
            self.preview_type.setText(spec.payload_type.value.upper())
            self.preview_icon.setText(icon)
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
