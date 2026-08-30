from pathlib import Path

from lnkup.core.evidence import compare_runs, list_runs
from lnkup.core.sessions import RunStore


def test_run_diff(tmp_path: Path):
    store = RunStore(tmp_path / "runs")
    store.start()
    store.append_event(
        {
            "protocol": "LLMNR",
            "event_type": "request_observed",
            "scope": "IN",
            "source": "192.0.2.1",
        }
    )
    store.finish()

    store.start()
    store.append_event(
        {
            "protocol": "SMB",
            "event_type": "authentication_observed",
            "scope": "IN",
            "source": "192.0.2.1",
        }
    )
    store.finish()

    runs = list_runs(tmp_path / "runs")
    diff = compare_runs(runs[1], runs[0])
    assert any(row["key"] == "SMB" and row["delta"] == 1 for row in diff["protocol"])
