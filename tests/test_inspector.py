import struct
from pathlib import Path

from lnkup.core.inspector import SHELL_LINK_CLSID, inspect_lnk


def test_inspector_recognizes_shell_link_header(tmp_path: Path):
    path = tmp_path / "sample.lnk"
    data = struct.pack("<I", 0x4C) + SHELL_LINK_CLSID + b"\x00" * (0x4C - 20)
    path.write_bytes(data)
    result = inspect_lnk(path)
    assert result.valid_header is True
    assert result.file_size == 0x4C


def test_inspector_rejects_random_file(tmp_path: Path):
    path = tmp_path / "not-a-link.lnk"
    path.write_bytes(b"hello")
    assert inspect_lnk(path).valid_header is False
