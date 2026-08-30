from __future__ import annotations

import shutil
from enum import Enum

from PySide6.QtCore import QObject, QProcess, Signal

from .events import parse_line
from .options import ResponderOptions


class ResponderState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ResponderController(QObject):
    state_changed = Signal(str)
    event_received = Signal(str, str, str)
    error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._process = QProcess(self)
        self._state = ResponderState.STOPPED

        self._process.started.connect(self._on_started)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_process_error)
        self._process.readyReadStandardOutput.connect(self._read_stdout)
        self._process.readyReadStandardError.connect(self._read_stderr)

    @property
    def state(self) -> ResponderState:
        return self._state

    def command_preview(self, options: ResponderOptions) -> str:
        return " ".join(options.argv())

    def start(self, options: ResponderOptions) -> None:
        if self._state not in {ResponderState.STOPPED, ResponderState.ERROR}:
            raise RuntimeError("Responder is already running or changing state")
        executable = shutil.which(options.executable)
        if executable is None:
            raise RuntimeError(
                f"Could not find '{options.executable}' in PATH. Install Responder or set its executable path."
            )
        argv = options.argv()
        self._set_state(ResponderState.STARTING)
        self._process.setProgram(executable)
        self._process.setArguments(argv[1:])
        self._process.start()

    def stop(self) -> None:
        if self._state not in {ResponderState.RUNNING, ResponderState.STARTING}:
            return
        self._set_state(ResponderState.STOPPING)
        self._process.terminate()
        if not self._process.waitForFinished(2500):
            self._process.kill()

    def _set_state(self, state: ResponderState) -> None:
        self._state = state
        self.state_changed.emit(state.value)

    def _on_started(self) -> None:
        self._set_state(ResponderState.RUNNING)

    def _on_finished(self, _exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
        self._set_state(ResponderState.STOPPED)

    def _on_process_error(self, error: QProcess.ProcessError) -> None:
        self._set_state(ResponderState.ERROR)
        self.error.emit(f"Responder process error: {error.name}")

    def _consume(self, text: str) -> None:
        for line in text.splitlines():
            event = parse_line(line)
            if event:
                self.event_received.emit(event.timestamp, event.level, event.message)

    def _read_stdout(self) -> None:
        data = bytes(self._process.readAllStandardOutput()).decode(errors="replace")
        self._consume(data)

    def _read_stderr(self) -> None:
        data = bytes(self._process.readAllStandardError()).decode(errors="replace")
        self._consume(data)
