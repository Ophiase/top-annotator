from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from textual.fuzzy import Matcher

from ...process.heuristics import is_kernel_thread
from ..process_info import ProcessInfo
from .process_row import TREE_SCOPE, ProcessRow, fold_key

PID_BONUS = 1.0


def matching_pids(processes: tuple[ProcessInfo, ...], query: str) -> set[int]:
    matcher = Matcher(query.strip())
    matched: set[int] = set()
    for process in processes:
        score = matcher.match(process_label(process))
        if str(process.pid).startswith(matcher.query):
            score += PID_BONUS
        if score > 0:
            matched.add(process.pid)
    return matched


def process_label(process: ProcessInfo) -> str:
    parts = [str(process.pid), process.name]
    executable = Path(process.exe).name
    if executable and executable != process.name:
        parts.append(executable)
    parts.extend(script_names(process.signature))
    return " ".join(parts)


def script_names(signature: str) -> tuple[str, ...]:
    parts = signature.split("|")
    if len(parts) < 3:
        return ()
    script = Path(parts[2]).name
    return (script,) if script else ()


def tree_rows(
    processes: tuple[ProcessInfo, ...],
    children: dict[int, list[ProcessInfo]],
    visible: set[int],
    folded: frozenset[str],
    scope: str = TREE_SCOPE,
) -> tuple[ProcessRow, ...]:
    rows: list[ProcessRow] = []
    roots = roots_of(processes, visible)
    for index, root in enumerate(roots):
        walk(
            children,
            root,
            0,
            (),
            index == len(roots) - 1,
            visible,
            folded,
            rows,
            set(),
            scope=scope,
        )
    return tuple(rows)


def section_tree(
    processes: tuple[ProcessInfo, ...],
    children: dict[int, list[ProcessInfo]],
    members: list[ProcessInfo],
    folded: frozenset[str],
    *,
    with_ancestors: bool,
    by_pid: dict[int, ProcessInfo],
    scope: str,
    stop: int | None = None,
    indent: str = "",
) -> tuple[ProcessRow, ...]:
    primary = {process.pid for process in members}
    visible = set(primary)
    if with_ancestors:
        for pid in primary:
            add_ancestors(pid, visible, by_pid, stop)
    rows: list[ProcessRow] = []
    roots = roots_of(processes, visible)
    for index, root in enumerate(roots):
        walk(
            children,
            root,
            0,
            (),
            index == len(roots) - 1,
            visible,
            folded,
            rows,
            set(),
            frozenset(visible - primary),
            scope=scope,
        )
    return tuple(replace(row, prefix=indent + row.prefix) for row in rows)


def roots_of(
    processes: tuple[ProcessInfo, ...],
    visible: set[int],
) -> list[ProcessInfo]:
    roots = [
        process
        for process in processes
        if process.pid in visible and process.ppid not in visible
    ]
    roots.sort(key=lambda process: (is_kernel_thread(process), process.pid))
    return roots


def walk(
    children: dict[int, list[ProcessInfo]],
    process: ProcessInfo,
    depth: int,
    ancestors_last: tuple[bool, ...],
    is_last: bool,
    visible: set[int],
    folded: frozenset[str],
    rows: list[ProcessRow],
    visited: set[int],
    context: frozenset[int] = frozenset(),
    *,
    scope: str,
) -> None:
    if process.pid in visited:
        return
    visited.add(process.pid)
    children_of_process = [
        child for child in children.get(process.pid, ()) if child.pid in visible
    ]
    key = fold_key(scope, process.pid)
    folded_here = key in folded
    rows.append(
        ProcessRow(
            process,
            depth,
            prefix(depth, ancestors_last, is_last)
            + marker(
                children_of_process,
                folded_here,
            ),
            bool(children_of_process),
            folded_here,
            process.pid in context,
            key,
        )
    )
    if not children_of_process or folded_here:
        return
    next_ancestors = (*ancestors_last, is_last)
    for index, child in enumerate(children_of_process):
        walk(
            children,
            child,
            depth + 1,
            next_ancestors,
            index == len(children_of_process) - 1,
            visible,
            folded,
            rows,
            visited,
            context,
            scope=scope,
        )


def prefix(
    depth: int,
    ancestors_last: tuple[bool, ...],
    is_last: bool,
) -> str:
    if depth == 0:
        return ""
    guides = "".join("   " if last else "│  " for last in ancestors_last)
    return guides + ("└─ " if is_last else "├─ ")


def marker(children: list[ProcessInfo], folded: bool) -> str:
    if not children:
        return "   "
    return "▸  " if folded else "▾  "


def add_ancestors(
    pid: int,
    visible: set[int],
    by_pid: dict[int, ProcessInfo],
    stop: int | None = None,
) -> None:
    """Add the ancestors of `pid`, up to but not including `stop`."""
    process = by_pid.get(pid)
    seen: set[int] = set()
    while process is not None and process.pid not in seen and process.ppid in by_pid:
        seen.add(process.pid)
        parent = by_pid[process.ppid]
        if parent.pid == stop:
            return
        visible.add(parent.pid)
        process = parent
