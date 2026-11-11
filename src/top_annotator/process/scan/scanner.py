from __future__ import annotations

from abc import ABC, abstractmethod

from ...core.process_info import ProcessInfo


class Scanner(ABC):
    @abstractmethod
    def scan(self) -> tuple[ProcessInfo, ...]:
        """Return one snapshot of the process table."""
