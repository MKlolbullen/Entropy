import json
from pathlib import Path

from lnkup.core.sessions import RunStore


def test_run_store(tmp_path: Path):
    store = RunStore(tmp_path / "runs")
    session = store.start({"interface": "eth0"})
    store.append_event({"level": "INFO", "message": "hello"})
    assert session.events_path.exists()
    record = json.loads(session.events_path.read_text(encoding="utf-8").strip())
    assert record["run_id"] == session.run_id
    assert record["message"] == "hello"
    store.finish({"exit_code": 0})
    manifest = json.loads(session.manifest_path.read_text(encoding="utf-8"))
    assert manifest["ended_at"] is not None
    assert manifest["result"]["exit_code"] == 0
