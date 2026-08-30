from __future__ import annotations

import configparser
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import psutil


@dataclass(slots=True)
class PreflightCheck:
    name: str
    status: str
    detail: str


@dataclass(slots=True)
class ServiceState:
    name: str
    enabled: bool | None
    source: str = "Responder.conf"


@dataclass(slots=True)
class PreflightReport:
    executable: str | None
    version: str | None
    config_path: Path | None
    privileged: bool
    checks: list[PreflightCheck] = field(default_factory=list)
    services: list[ServiceState] = field(default_factory=list)


KNOWN_PORTS: dict[str, tuple[int, ...]] = {
    "SMB": (445,), "HTTP": (80,), "HTTPS": (443,), "DNS": (53,),
    "LDAP": (389,), "Kerberos": (88,), "FTP": (21,), "SMTP": (25,),
    "POP3": (110,), "IMAP": (143,), "MSSQL": (1433,), "MySQL": (3306,),
    "RDP": (3389,), "WinRM": (5985, 5986), "MQTT": (1883,), "SNMP": (161,),
}

_SERVICE_KEYS = {
    "SQL": "MSSQL", "SMB": "SMB", "RDP": "RDP", "KERBEROS": "Kerberos",
    "FTP": "FTP", "POP": "POP3", "POP3": "POP3", "SMTP": "SMTP",
    "IMAP": "IMAP", "HTTP": "HTTP", "HTTPS": "HTTPS", "DNS": "DNS",
    "LDAP": "LDAP", "WINRM": "WinRM", "SNMP": "SNMP", "MQTT": "MQTT",
    "MYSQL": "MySQL", "QUIC": "QUIC", "DCERPC": "DCERPC",
}


def resolve_executable(value: str = "responder") -> str | None:
    expanded = str(Path(value).expanduser())
    if os.sep in expanded or (os.altsep and os.altsep in expanded):
        path = Path(expanded)
        return str(path.resolve()) if path.is_file() else None
    return shutil.which(value)


def detect_version(executable: str | None) -> str | None:
    if not executable:
        return None
    try:
        proc = subprocess.run(
            [executable, "-h"], capture_output=True, text=True, timeout=3, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = f"{proc.stdout}\n{proc.stderr}"
    for pattern in (
        r"(?i)Responder\s+([0-9]+(?:\.[0-9A-Za-z_-]+)+)",
        r"(?i)version\s*[:=]?\s*([0-9]+(?:\.[0-9A-Za-z_-]+)+)",
    ):
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    first = next((line.strip() for line in text.splitlines() if "responder" in line.lower()), None)
    return first[:100] if first else None


def find_config(executable: str | None = None) -> Path | None:
    candidates: list[Path] = []
    if executable:
        exe = Path(executable).resolve()
        candidates.extend([
            exe.parent / "Responder.conf",
            exe.parent.parent / "share" / "responder" / "Responder.conf",
        ])
    candidates.extend([
        Path.cwd() / "Responder.conf",
        Path("/etc/responder/Responder.conf"),
        Path("/usr/share/responder/Responder.conf"),
        Path("/opt/Responder/Responder.conf"),
    ])
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.expanduser()
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            return candidate.resolve()
    return None


def parse_service_states(path: Path | None) -> list[ServiceState]:
    if not path or not path.is_file():
        return []
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read(path, encoding="utf-8")
    except (configparser.Error, OSError):
        return []

    states: dict[str, ServiceState] = {}
    bool_values = {"on", "off", "true", "false", "yes", "no", "1", "0"}
    true_values = {"on", "true", "yes", "1"}
    for section in parser.sections():
        for key, value in parser.items(section):
            normalized = key.strip().upper().replace("-", "").replace("_", "")
            name = _SERVICE_KEYS.get(normalized)
            if not name:
                continue
            raw = value.strip().lower()
            enabled = raw in true_values if raw in bool_values else None
            states[name] = ServiceState(name=name, enabled=enabled, source=section)
    return sorted(states.values(), key=lambda item: item.name.lower())


def is_privileged() -> bool:
    if os.name == "nt":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return hasattr(os, "geteuid") and os.geteuid() == 0


def listening_ports() -> set[int]:
    ports: set[int] = set()
    try:
        connections = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, psutil.Error):
        return ports
    for conn in connections:
        if conn.status == psutil.CONN_LISTEN and conn.laddr:
            ports.add(int(conn.laddr.port))
    return ports


def run_preflight(executable_value: str = "responder") -> PreflightReport:
    executable = resolve_executable(executable_value)
    version = detect_version(executable)
    config = find_config(executable)
    privileged = is_privileged()
    services = parse_service_states(config)
    checks: list[PreflightCheck] = [
        PreflightCheck("Executable", "PASS" if executable else "FAIL", executable or f"'{executable_value}' not found"),
        PreflightCheck("Version", "PASS" if version else "WARN", version or "Version could not be identified from help output"),
        PreflightCheck("Configuration", "PASS" if config else "WARN", str(config) if config else "Responder.conf not found"),
        PreflightCheck("Privileges", "PASS" if privileged else "WARN", "Elevated" if privileged else "Not elevated; low ports may be unavailable"),
    ]

    occupied = listening_ports()
    relevant: list[str] = []
    enabled_by_name = {service.name: service.enabled for service in services}
    for service, ports in KNOWN_PORTS.items():
        if enabled_by_name.get(service) is False:
            continue
        collisions = sorted(set(ports) & occupied)
        if collisions:
            relevant.append(f"{service}: {', '.join(map(str, collisions))}")
    checks.append(PreflightCheck(
        "Port conflicts", "WARN" if relevant else "PASS",
        "; ".join(relevant) if relevant else "No known listener conflicts detected",
    ))

    return PreflightReport(
        executable=executable, version=version, config_path=config,
        privileged=privileged, checks=checks, services=services,
    )
