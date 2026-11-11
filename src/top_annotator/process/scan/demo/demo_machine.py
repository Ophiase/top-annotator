from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ....audit import AuditStore
from ....audit.routing.os_release import OS_RELEASE_VARIABLE
from .demo_scanner import DemoScanner

DEMO_ROOT = Path(__file__).parent
DEMO_AUDIT = DEMO_ROOT / "audit"
DEMO_OS_RELEASE = DEMO_ROOT / "os-release"
DEMO_NOTICE = "DEMO DATA: a fictional machine, changes discarded on exit"


@dataclass(frozen=True, slots=True)
class DemoMachine:
    """A fictional host: its processes, its base audit and its distribution.

    `data_dir` receives the session and the journal; the caller owns it and
    throws it away, so every run starts from the same state.
    """

    data_dir: Path

    def store(self) -> AuditStore:
        os.environ[OS_RELEASE_VARIABLE] = str(DEMO_OS_RELEASE)
        return AuditStore.load(
            DEMO_AUDIT,
            session_path=self.data_dir / "session.yaml",
            scopes=(),
        )

    def scanner(self) -> DemoScanner:
        return DemoScanner()
