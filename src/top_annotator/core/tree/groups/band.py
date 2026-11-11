from __future__ import annotations

from collections.abc import Mapping

from ....process.heuristics import is_kernel_thread
from ...annotation import Annotation
from ...process_info import ProcessInfo
from ...section import Section
from ...section_header import SectionHeader, key_of
from ..process_row import TREE_SCOPE, Row, fold_key
from ..traversal import section_tree
from .kernel import KERNEL_FAMILIES, OTHER, kernel_rows
from .providers import (
    GROUP_ORDER,
    KERNEL,
    OPEN_GROUPS,
    common_chain,
    provider_groups,
)


def default_folded(processes: tuple[ProcessInfo, ...]) -> frozenset[str]:
    """The risky groups start open; the system groups, the kernel families
    and the kernel thread root start folded."""
    safe = Section.SAFE
    roots = [
        process.pid
        for process in processes
        if is_kernel_thread(process) and process.ppid == 0
    ]
    return frozenset({
        *(key_of(safe, group) for group in GROUP_ORDER if group not in OPEN_GROUPS),
        *(key_of(safe, f"{KERNEL}/{family}") for family in (*KERNEL_FAMILIES, OTHER)),
        *(fold_key(TREE_SCOPE, pid) for pid in roots),
    })


def safe_band_rows(
    members: list[ProcessInfo],
    annotations: Mapping[str, Annotation],
    folded: frozenset[str],
    *,
    processes: tuple[ProcessInfo, ...],
    children: dict[int, list[ProcessInfo]],
    by_pid: dict[int, ProcessInfo],
) -> list[Row]:
    """The SAFE band, one header per provider group. A group's shared
    ancestors go into its header; below them it is a tree, with the parents
    from other groups shown dim, as context."""
    rows: list[Row] = []
    for group, grouped in provider_groups(members, annotations, by_pid):
        chain = common_chain(grouped, by_pid)
        header = SectionHeader.build(
            Section.SAFE,
            grouped,
            folded,
            group,
            tuple(process.name for process in chain),
        )
        rows.append(header)
        if header.folded:
            continue
        if group == KERNEL:
            rows.extend(kernel_rows(grouped, folded))
            continue
        rows.extend(
            section_tree(
                processes,
                children,
                grouped,
                folded,
                with_ancestors=True,
                stop=chain[0].pid if chain else None,
                by_pid=by_pid,
                scope=header.key,
                indent="  ",
            )
        )
    return rows
