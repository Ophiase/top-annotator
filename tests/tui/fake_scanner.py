from __future__ import annotations

from top_annotator.core.process_info import ProcessInfo
from top_annotator.process.scan import Scanner

from ..factories import process

SYSTEMD = "systemd|/usr/lib/systemd/systemd"


class FakeScanner(Scanner):
    def __init__(self) -> None:
        self.scans = 0

    def scan(self) -> tuple[ProcessInfo, ...]:
        self.scans += 1
        return (
            process(
                1,
                0,
                name="systemd",
                exe="/usr/lib/systemd/systemd",
                signature=SYSTEMD,
            ),
            process(2, 1, name="app", exe="/usr/bin/app", signature="app|/usr/bin/app"),
        )
