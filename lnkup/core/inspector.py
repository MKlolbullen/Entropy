from __future__ import annotations

import re
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SHELL_LINK_HEADER_SIZE = 0x4C
SHELL_LINK_CLSID = bytes.fromhex("0114020000000000c000000000000046")


@dataclass(slots=True)
class LnkInspection:
    path: Path
    valid_header: bool
    file_size: int
    target_path: str | None = None
    arguments: str | None = None
    working_directory: str | None = None
    icon_location: str | None = None
    description: str | None = None
    unc_paths: list[str] = field(default_factory=list)
    strings: list[str] = field(default_factory=list)
    parser: str = "fallback"


def inspect_lnk(path: str | Path) -> LnkInspection:
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise ValueError("LNK file does not exist")
    data = file_path.read_bytes()
    valid = len(data) >= SHELL_LINK_HEADER_SIZE and data[:4] == struct.pack("<I", SHELL_LINK_HEADER_SIZE) and data[4:20] == SHELL_LINK_CLSID
    result = LnkInspection(
        path=file_path,
        valid_header=valid,
        file_size=len(data),
        unc_paths=_extract_unc_paths(data),
        strings=_extract_strings(data)[:100],
    )
    if not valid:
        return result

    if sys.platform.startswith("win") and _inspect_windows(file_path, result):
        return result
    if _inspect_pylnk3(file_path, result):
        return result
    _infer_fields(result)
    return result


def _inspect_windows(path: Path, result: LnkInspection) -> bool:
    try:
        import win32com.client  # type: ignore

        shell = win32com.client.Dispatch("WScript.Shell")
        link = shell.CreateShortcut(str(path))
        result.target_path = _clean(getattr(link, "TargetPath", None))
        result.arguments = _clean(getattr(link, "Arguments", None))
        result.working_directory = _clean(getattr(link, "WorkingDirectory", None))
        result.icon_location = _clean(getattr(link, "IconLocation", None))
        result.description = _clean(getattr(link, "Description", None))
        result.parser = "win32com"
        return True
    except Exception:
        return False


def _inspect_pylnk3(path: Path, result: LnkInspection) -> bool:
    try:
        import pylnk3  # type: ignore

        parser = getattr(pylnk3, "parse", None)
        if not callable(parser):
            return False
        link = parser(str(path))
        fields = {
            "target_path": ("path", "target", "target_path"),
            "arguments": ("arguments", "command_line_arguments"),
            "working_directory": ("work_dir", "working_directory"),
            "icon_location": ("icon", "icon_file", "icon_location"),
            "description": ("description",),
        }
        for output, candidates in fields.items():
            for name in candidates:
                value = getattr(link, name, None)
                if value:
                    setattr(result, output, str(value))
                    break
        result.parser = "pylnk3"
        return True
    except Exception:
        return False


def _extract_unc_paths(data: bytes) -> list[str]:
    found: list[str] = []
    ascii_text = data.decode("latin1", errors="ignore")
    unicode_text = data.decode("utf-16le", errors="ignore")
    for text in (ascii_text, unicode_text):
        for match in re.findall(r"\\\\[^\x00\r\n\t<>\"|?* ]+", text):
            candidate = match.rstrip(".,;)")
            if candidate not in found:
                found.append(candidate)
    return found[:50]


def _extract_strings(data: bytes) -> list[str]:
    values: list[str] = []
    for raw in re.findall(rb"[\x20-\x7e]{4,}", data):
        text = raw.decode("ascii", errors="ignore")
        if text not in values:
            values.append(text)
    for raw in re.findall(rb"(?:[\x20-\x7e]\x00){4,}", data):
        text = raw.decode("utf-16le", errors="ignore")
        if text not in values:
            values.append(text)
    return values


def _infer_fields(result: LnkInspection) -> None:
    if result.unc_paths and not result.icon_location:
        result.icon_location = result.unc_paths[0]
    for value in result.strings:
        lowered = value.lower()
        if not result.target_path and lowered.endswith((".exe", ".cmd", ".bat", ".ps1")):
            result.target_path = value
        if not result.arguments and (" /c " in lowered or lowered.startswith("/c ")):
            result.arguments = value


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
