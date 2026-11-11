from __future__ import annotations

import re
from pathlib import Path

SYSTEMD_ESCAPE = re.compile(r"\\x([0-9a-f]{2})")


def read_unit(process_directory: Path) -> str:
    """The last cgroup component: `ollama.service`, `app-…scope`, or empty."""
    try:
        raw = (process_directory / "cgroup").read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in raw.splitlines():
        if line.startswith("0::"):
            return unescape(line.rsplit("/", 1)[-1])
    return ""


def unescape(unit: str) -> str:
    return SYSTEMD_ESCAPE.sub(lambda match: chr(int(match.group(1), 16)), unit)
