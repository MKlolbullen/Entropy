from pathlib import Path

from lnkup.core.evidence import export_bundle, list_runs, load_events
from lnkup.core.sessions import RunStore


def test_evidence_browser_and_export(tmp_path: Path):
    store = RunStore(tmp_path / "runs")
    store.start({"engagement": {"name": "Lab"}})
    store.append_event(
        {
            "protocol": "LLMNR",
            "event_type": "request_observed",
            "scope": "IN",
            "message": "sample",
        }
    )
    store.finish({"exit_code": 0})
    runs = list_runs(tmp_path / "runs")
    assert len(runs) == 1
    assert load_events(runs[0])[0]["protocol"] == "LLMNR"
    bundle = export_bundle(runs[0], tmp_path / "bundle.zip")
    assert bundle.exists()
