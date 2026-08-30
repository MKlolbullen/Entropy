from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class PayloadType(str, Enum):
    NTLM = "ntlm"
    ENVIRONMENT = "environment"


@dataclass(slots=True)
class LnkSpec:
    host: str
    output: Path
    payload_type: PayloadType = PayloadType.NTLM
    environment_variables: list[str] = field(default_factory=list)
    execute: str = r"C:\Windows\explorer.exe ."


@dataclass(slots=True)
class GeneratedLnk:
    output: Path
    icon_location: str
    arguments: str


@dataclass(slots=True)
class InterfaceInfo:
    name: str
    ipv4: str | None = None
    ipv6: str | None = None
