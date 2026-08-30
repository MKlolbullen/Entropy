from lnkup.responder.events import parse_line


def test_protocol_and_source_parsing():
    event = parse_line("[LLMNR] Poisoned answer sent to 192.0.2.44 for name FILESERVER")
    assert event is not None
    assert event.protocol == "LLMNR"
    assert event.source == "192.0.2.44"
    assert event.event_type == "name_resolution_observed"
    assert event.name == "FILESERVER"


def test_sensitive_material_is_redacted():
    event = parse_line("[SMB] NTLMv2 Hash: deadbeefcafebabe")
    assert event is not None
    assert "deadbeefcafebabe" not in event.message
    assert "<redacted>" in event.message
