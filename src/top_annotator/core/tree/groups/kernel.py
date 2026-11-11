from __future__ import annotations

from ...process_info import ProcessInfo
from ...section import Section
from ...section_header import SectionHeader
from ..process_row import ProcessRow, Row, fold_key
from .providers import KERNEL

OTHER = "other"

KERNEL_FAMILIES: dict[str, tuple[tuple[str, ...], str]] = {
    "kworker": (("kworker/", "pool_workqueue"), "generic work queues"),
    "irq": (("irq/",), "hardware interrupt handlers, one per device line"),
    "cpu": (
        ("migration/", "ksoftirqd/", "idle_inject/", "cpuhp/"),
        "per-CPU: task migration, deferred interrupts, power, hotplug",
    ),
    "memory": (
        ("kswapd", "kcompactd", "khugepaged", "ksmd", "oom_reaper"),
        "memory reclaim, compaction, huge pages, out-of-memory",
    ),
    "storage": (
        ("jbd2/", "dmcrypt_write", "kcryptd", "ecryptfs", "kdevtmpfs", "writeback"),
        "filesystem journals, disk encryption, device nodes",
    ),
    "gpu": (("card", "nvidia", "i915", "amdgpu"), "graphics driver"),
    "rcu": (("rcu_", "rcub/", "rcuop/"), "the kernel's internal synchronisation"),
    "monitoring": (
        ("watchdogd", "khungtaskd", "kauditd", "kprobe"),
        "watchdog, hung-task detector, audit, probes",
    ),
    "devices": (
        ("spi", "hwrng", "krfcommd", "napi"),
        "buses, random-number source, Bluetooth, network polling",
    ),
}


def kernel_family(name: str) -> str:
    return next(
        (
            family
            for family, (prefixes, _) in KERNEL_FAMILIES.items()
            if name.startswith(prefixes)
        ),
        OTHER,
    )


def kernel_rows(members: list[ProcessInfo], folded: frozenset[str]) -> list[Row]:
    """The kernel group: `kthreadd` itself, then its threads by family."""
    safe = Section.SAFE
    rows: list[Row] = [
        ProcessRow(root, 0, "     ", False, False, key=fold_key(KERNEL, root.pid))
        for root in members
        if root.ppid == 0
    ]
    families: dict[str, list[ProcessInfo]] = {}
    for thread in members:
        if thread.ppid != 0:
            families.setdefault(kernel_family(thread.name), []).append(thread)
    for family in (*KERNEL_FAMILIES, OTHER):
        threads = families.get(family)
        if not threads:
            continue
        header = SectionHeader.build(safe, threads, folded, f"{KERNEL}/{family}")
        rows.append(header)
        if not header.folded:
            rows.extend(
                ProcessRow(
                    thread,
                    1,
                    "       ",
                    False,
                    False,
                    key=fold_key(header.key, thread.pid),
                )
                for thread in sorted(threads, key=lambda thread: thread.name)
            )
    return rows
