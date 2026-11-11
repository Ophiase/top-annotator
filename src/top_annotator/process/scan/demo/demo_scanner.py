from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from ....core.process_info import ProcessInfo
from ...signature import process_signature
from ..scanner import Scanner

DEMO_PROCESSES = Path(__file__).parent / "processes.yaml"
MEBIBYTE = 1024 * 1024


class DemoScanner(Scanner):
    def __init__(self, path: Path = DEMO_PROCESSES) -> None:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self._processes = tuple(
            _process(entry) for entry in payload.get("processes", ())
        )

    def scan(self) -> tuple[ProcessInfo, ...]:
        return self._processes


def _process(entry: Mapping[str, Any]) -> ProcessInfo:
    name = str(entry["name"])
    exe = str(entry.get("exe", ""))
    cmdline = tuple(str(part) for part in entry.get("cmdline", ()))
    return ProcessInfo(
        pid=int(entry["pid"]),
        ppid=int(entry["ppid"]),
        name=name,
        exe=exe,
        cmdline=cmdline,
        user=str(entry.get("user", "demo")),
        state=str(entry.get("state", "S")),
        threads=int(entry.get("threads", 1)),
        rss_bytes=int(entry.get("rss_mib", 0)) * MEBIBYTE,
        cpu_percent=float(entry.get("cpu", 0.0)),
        signature=process_signature(name, exe, cmdline),
        unit=str(entry.get("unit", "")),
        listens=tuple(str(address) for address in entry.get("listens", ())),
    )
