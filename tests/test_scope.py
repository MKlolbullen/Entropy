import pytest

from lnkup.core.scope import EngagementScope, parse_network_text


def test_scope_classification():
    scope = EngagementScope("Lab", ["192.0.2.0/24"], ["192.0.2.5/32"])
    assert scope.classify("192.0.2.10") == "IN"
    assert scope.classify("192.0.2.5") == "OUT"
    assert scope.classify("198.51.100.1") == "OUT"
    assert scope.classify(None) == "UNKNOWN"


def test_scope_parser_normalizes():
    assert parse_network_text("192.0.2.3/24\n198.51.100.0/24") == ["192.0.2.0/24", "198.51.100.0/24"]


def test_invalid_scope_rejected():
    with pytest.raises(ValueError):
        parse_network_text("not-a-network")
