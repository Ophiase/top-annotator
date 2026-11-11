from __future__ import annotations

import os
import pwd
import time
from pathlib import Path

from ...core.process_info import ProcessInfo
from ..signature import process_signature
from .scanner import Scanner
from .sockets import listening_sockets, listens_of
from .stat import ProcessStat
from .units import read_unit

PROC = Path("/proc")
CLOCK_TICKS = os.sysconf("SC_CLK_TCK")
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")


class ProcessScanner(Scanner):
    def __init__(self) -> None:
        self._previous_ticks: dict[int, int] = {}
        self._previous_time = time.monotonic()

    def scan(self) -> tuple[ProcessInfo, ...]:
        now = time.monotonic()
        elapsed = max(now - self._previous_time, 0.001)
        processes: list[ProcessInfo] = []
        current_ticks: dict[int, int] = {}
        sockets = listening_sockets(PROC)
        for entry in _process_entries():
            pid = int(entry.name)
            stat = _read_stat(pid)
            if stat is None:
                continue
            current_ticks[pid] = stat.ticks
            cmdline = _read_cmdline(pid)
            exe = _read_link(pid, "exe")
            processes.append(
                ProcessInfo(
                    pid=pid,
                    ppid=stat.ppid,
                    name=stat.name,
                    exe=exe,
                    cmdline=cmdline,
                    user=_user_name(pid),
                    state=stat.state,
                    threads=stat.threads,
                    rss_bytes=stat.rss_pages * PAGE_SIZE,
                    cpu_percent=self._cpu_percent(pid, stat.ticks, elapsed),
                    signature=process_signature(stat.name, exe, cmdline),
                    unit=read_unit(PROC / entry.name),
                    listens=listens_of(PROC / entry.name, sockets),
                )
            )
        self._previous_ticks = current_ticks
        self._previous_time = now
        return tuple(sorted(processes, key=lambda process: process.pid))

    def _cpu_percent(self, pid: int, ticks: int, elapsed: float) -> float:
        previous = self._previous_ticks.get(pid)
        if previous is None:
            return 0.0
        used = max(ticks - previous, 0) / CLOCK_TICKS
        return min(used / elapsed * 100.0, 100.0 * (os.cpu_count() or 1))


def _process_entries() -> tuple[os.DirEntry[str], ...]:
    try:
        with os.scandir(PROC) as entries:
            return tuple(entry for entry in entries if entry.name.isdigit())
    except OSError:
        return ()


def _read_stat(pid: int) -> ProcessStat | None:
    try:
        raw = (PROC / str(pid) / "stat").read_text(encoding="utf-8")
    except OSError:
        return None
    opening = raw.find("(")
    closing = raw.rfind(")")
    if opening == -1 or closing == -1:
        return None
    fields = raw[closing + 2 :].split()
    if len(fields) < 22:
        return None
    return ProcessStat(
        name=raw[opening + 1 : closing],
        state=fields[0],
        ppid=int(fields[1]),
        ticks=int(fields[11]) + int(fields[12]),
        threads=int(fields[17]),
        rss_pages=int(fields[21]),
    )


def _read_cmdline(pid: int) -> tuple[str, ...]:
    try:
        raw = (PROC / str(pid) / "cmdline").read_bytes()
    except OSError:
        return ()
    return tuple(
        part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part
    )


def _read_link(pid: int, name: str) -> str:
    try:
        return str((PROC / str(pid) / name).readlink())
    except OSError:
        return ""


def _user_name(pid: int) -> str:
    try:
        status = (PROC / str(pid) / "status").read_text(encoding="utf-8")
    except OSError:
        return "?"
    uid = _uid_from_status(status)
    if uid is None:
        return "?"
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def _uid_from_status(status: str) -> int | None:
    for line in status.splitlines():
        if line.startswith("Uid:"):
            return int(line.split()[1])
    return None
