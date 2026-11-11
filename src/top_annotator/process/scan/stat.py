from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProcessStat:
    name: str
    state: str
    ppid: int
    ticks: int
    threads: int
    rss_pages: int
