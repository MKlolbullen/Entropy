from __future__ import annotations

import shutil
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

from lnkup.core.scope import EngagementScope
from lnkup.core.sessions import RunStore
from .correlation import EventCorrelator
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
    event_received = Signal(object)
    session_changed = Signal(str)
    error = Signal(str)

    def __init__(self, parent: QObject | None = None, runs_root: Path | str = "runs") -> None:
        super().__init__(parent)
        self._process = QProcess(self)
        self._state = ResponderState.STOPPED
        self.runs = RunStore(runs_root)
        self.scope = EngagementScope()
        self.correlator = EventCorrelator()
        self._process.started.connect(self._on_started)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_process_error)
        self._process.readyReadStandardOutput.connect(self._read_stdout)
        self._process.readyReadStandardError.connect(self._read_stderr)

    @property
    def state(self) -> ResponderState:
        return self._state

    @property
    def run_id(self) -> str | None:
        return self.runs.current.run_id if self.runs.current else None

    def set_scope(self, scope: EngagementScope) -> None:
        if self._state not in {ResponderState.STOPPED, ResponderState.ERROR}:
            raise RuntimeError("Scope cannot be changed while an analysis run is active")
        self.scope = scope

    def command_preview(self, options: ResponderOptions) -> str:
        return " ".join(options.argv())

    def start(self, options: ResponderOptions) -> None:
        if self._state not in {ResponderState.STOPPED, ResponderState.ERROR}:
            raise RuntimeError("Responder is already running or changing state")
        executable = shutil.which(options.executable)
        if executable is None and Path(options.executable).expanduser().is_file():
            executable = str(Path(options.executable).expanduser().resolve())
        if executable is None:
            raise RuntimeError(f"Could not find '{options.executable}' in PATH")
        argv = options.argv()
        self.correlator.reset()
        session = self.runs.start({
            "component": "responder", "mode": "analyze", "interface": options.interface,
            "command": argv, "executable": executable, "engagement": self.scope.to_dict(),
        })
        self.session_changed.emit(session.run_id)
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

    def _on_finished(self, exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
        self.runs.finish({"exit_code": exit_code})
        self.session_changed.emit("")
        self._set_state(ResponderState.STOPPED)

    def _on_process_error(self, error: QProcess.ProcessError) -> None:
        self.runs.finish({"process_error": error.name})
        self.session_changed.emit("")
        self._set_state(ResponderState.ERROR)
        self.error.emit(f"Responder process error: {error.name}")

    def _consume(self, text: str) -> None:
        for line in text.splitlines():
            event = parse_line(line)
            if not event:
                continue
            event.scope = self.scope.classify(event.source)
            correlation = self.correlator.correlate(event)
            event.correlation_id = correlation.correlation_id
            event.correlation_count = correlation.count
            self.runs.append_event(event.to_dict())
            self.event_received.emit(event)

    def _read_stdout(self) -> None:
        self._consume(bytes(self._process.readAllStandardOutput()).decode(errors="replace"))

    def _read_stderr(self) -> None:
        self._consume(bytes(self._process.readAllStandardError()).decode(errors="replace"))
