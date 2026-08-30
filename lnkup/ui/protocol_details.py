from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QPlainTextEdit, QVBoxLayout, QWidget


class ProtocolDetailPane(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(250)
        root = QVBoxLayout(self)
        box = QGroupBox("Selected event")
        form = QFormLayout(box)
        self.protocol = QLabel("—")
        self.event_type = QLabel("—")
        self.source = QLabel("—")
        self.scope = QLabel("—")
        self.identity = QLabel("—")
        self.name = QLabel("—")
        self.correlation = QLabel("—")
        self.context = QLabel("Select an event to see protocol-specific context.")
        self.context.setWordWrap(True)
        for label, widget in (
            ("Protocol", self.protocol),
            ("Type", self.event_type),
            ("Source", self.source),
            ("Scope", self.scope),
            ("Identity", self.identity),
            ("Name", self.name),
            ("Correlation", self.correlation),
            ("Context", self.context),
        ):
            form.addRow(label, widget)
        root.addWidget(box)
        raw = QGroupBox("Redacted event")
        raw_layout = QVBoxLayout(raw)
        self.message = QPlainTextEdit()
        self.message.setReadOnly(True)
        self.message.setMaximumHeight(95)
        raw_layout.addWidget(self.message)
        root.addWidget(raw)

    def set_event(self, event: dict) -> None:
        protocol = str(event.get("protocol", "SYSTEM"))
        self.protocol.setText(protocol)
        self.event_type.setText(str(event.get("event_type", "log")))
        self.source.setText(str(event.get("source") or "—"))
        self.scope.setText(str(event.get("scope", "UNKNOWN")))
        self.identity.setText(str(event.get("identity") or "—"))
        self.name.setText(str(event.get("name") or "—"))
        cid = event.get("correlation_id") or "—"
        count = event.get("correlation_count") or 0
        self.correlation.setText(f"{cid} · {count} event(s)" if cid != "—" else "—")
        self.context.setText(self._context(protocol, event))
        self.message.setPlainText(str(event.get("message", "")))

    @staticmethod
    def _context(protocol: str, event: dict) -> str:
        p = protocol.upper()
        if p in {"LLMNR", "NBT-NS", "NBTNS", "MDNS"}:
            return "Name-resolution observation. Review the queried name, source, scope, and nearby correlated SMB/HTTP events."
        if p == "SMB":
            return "SMB observation. Correlate source and identity with preceding name-resolution events; credential material remains redacted."
        if p in {"HTTP", "HTTPS"}:
            return "Web-protocol observation. Use correlation and scope rather than raw authentication material for analysis."
        if p == "DNS":
            return "DNS observation. Review requested names and correlation frequency for repeated or unexpected resolution behavior."
        return "Generic structured event. Fields are normalized from the redacted Responder output."
