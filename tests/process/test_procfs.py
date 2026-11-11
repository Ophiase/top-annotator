from __future__ import annotations

import os

from top_annotator.process.scan import ProcessScanner


def test_live_scan_contains_the_current_process() -> None:
    processes = ProcessScanner().scan()

    assert os.getpid() in {process.pid for process in processes}
