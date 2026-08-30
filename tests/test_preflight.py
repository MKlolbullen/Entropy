from pathlib import Path

from lnkup.responder.preflight import parse_service_states


def test_parse_responder_services(tmp_path: Path):
    conf = tmp_path / "Responder.conf"
    conf.write_text(
        """[Responder Core]\nSMB = On\nHTTP = Off\nLDAP = On\nMQTT = Off\n""",
        encoding="utf-8",
    )
    states = {item.name: item.enabled for item in parse_service_states(conf)}
    assert states["SMB"] is True
    assert states["HTTP"] is False
    assert states["LDAP"] is True
    assert states["MQTT"] is False
