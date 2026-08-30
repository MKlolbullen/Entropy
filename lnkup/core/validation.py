from __future__ import annotations

import ipaddress
import re

from .models import LnkSpec, PayloadType

_HOST_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_host(host: str) -> str:
    host = host.strip()
    if not host:
        raise ValueError("Listener host cannot be empty")
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    if not _HOST_RE.fullmatch(host):
        raise ValueError("Listener host contains unsupported characters")
    return host


def validate_spec(spec: LnkSpec) -> None:
    validate_host(spec.host)
    if spec.output.suffix.lower() != ".lnk":
        raise ValueError("Output must use a .lnk extension")
    if spec.payload_type is PayloadType.ENVIRONMENT:
        if not spec.environment_variables:
            raise ValueError("Environment payload requires at least one variable")
        invalid = [v for v in spec.environment_variables if not _VAR_RE.fullmatch(v)]
        if invalid:
            raise ValueError(f"Invalid environment variable name(s): {', '.join(invalid)}")
    if not spec.execute.strip():
        raise ValueError("Execute command cannot be empty")
    spec.output.parent.mkdir(parents=True, exist_ok=True)
