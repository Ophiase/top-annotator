from __future__ import annotations

from top_annotator.core.process_info import ProcessInfo


def process(
    pid: int,
    ppid: int = 0,
    *,
    name: str = "proc",
    exe: str = "/usr/bin/proc",
    cmdline: tuple[str, ...] = (),
    signature: str | None = None,
    unit: str = "",
    listens: tuple[str, ...] = (),
    user: str = "tester",
) -> ProcessInfo:
    return ProcessInfo(
        pid=pid,
        ppid=ppid,
        name=name,
        exe=exe,
        cmdline=cmdline,
        user=user,
        state="S",
        threads=1,
        rss_bytes=1024,
        cpu_percent=0.0,
        signature=signature or f"{name}|{exe}|{pid}",
        unit=unit,
        listens=listens,
    )
