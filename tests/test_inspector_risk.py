from pathlib import Path

from lnkup.core.inspector import LnkInspection, _analyze_risk


def test_remote_reference_is_high_risk(tmp_path: Path):
    result = LnkInspection(path=tmp_path / "a.lnk", valid_header=True, file_size=10, icon_location=r"\\server\share\a.ico", unc_paths=[r"\\server\share\a.ico"])
    _analyze_risk(result)
    assert result.risk_score >= 40
    assert any(item.name == "Remote resource reference" for item in result.indicators)
