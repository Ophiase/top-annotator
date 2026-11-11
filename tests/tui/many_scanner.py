from __future__ import annotations

from top_annotator.core.process_info import ProcessInfo
from top_annotator.process.scan import Scanner

from ..factories import process


class ManyScanner(Scanner):
    def scan(self) -> tuple[ProcessInfo, ...]:
        return tuple(
            process(
                100 + index,
                0,
                name=f"app{index}",
                exe="/usr/bin/app",
                signature=f"app{index}|/usr/bin/app",
            )
            for index in range(60)
        )
