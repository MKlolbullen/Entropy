import pytest

from lnkup.responder.options import ResponderOptions


def test_analyze_command():
    opts = ResponderOptions(interface="eth0", verbose=True)
    assert opts.argv() == ["responder", "-I", "eth0", "-A", "-v"]


def test_active_mode_not_enabled():
    with pytest.raises(ValueError):
        ResponderOptions(interface="eth0", analyze=False).argv()
