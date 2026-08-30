from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ResponderOptions:
    interface: str
    analyze: bool = True
    verbose: bool = True
    quiet: bool = False
    executable: str = "responder"

    def argv(self) -> list[str]:
        if not self.analyze:
            raise ValueError(
                "Active poisoning mode is intentionally not enabled in this initial LNK-NG branch"
            )
        args = [self.executable, "-I", self.interface, "-A"]
        if self.verbose:
            args.append("-v")
        if self.quiet:
            args.append("-Q")
        return args
