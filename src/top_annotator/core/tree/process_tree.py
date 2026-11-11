from __future__ import annotations

from collections.abc import Iterable, Mapping

from ...process.heuristics import is_kernel_thread, is_zombie
from ..annotation import SHELLS, Annotation
from ..process_info import ProcessInfo
from ..section import SECTION_ORDER, Section, section_for, typed_in_terminal
from ..section_header import SectionHeader
from .filters import ALL, NETWORK, UNREVIEWED
from .groups import default_folded, safe_band_rows
from .process_row import TREE_SCOPE, ProcessRow, Row, fold_key
from .traversal import (
    add_ancestors,
    matching_pids,
    section_tree,
    tree_rows,
)
from .vouching import vouched


class ProcessTree:
    def __init__(self, processes: Iterable[ProcessInfo]) -> None:
        self.processes = tuple(processes)
        self._by_pid = {process.pid: process for process in self.processes}
        self._children: dict[int, list[ProcessInfo]] = {}
        for process in self.processes:
            self._children.setdefault(process.ppid, []).append(process)
        for children in self._children.values():
            children.sort(key=lambda process: process.pid)

    def rows(
        self,
        *,
        annotations: Mapping[str, Annotation],
        query: str = "",
        folded: frozenset[str] = frozenset(),
        view_filter: str = ALL,
        tree_view: bool = True,
    ) -> tuple[ProcessRow, ...]:
        visible = self._visible_pids(
            annotations=annotations,
            query=query,
            view_filter=view_filter,
        )
        if not tree_view:
            return tuple(
                ProcessRow(
                    process, 0, "", False, False, key=fold_key(TREE_SCOPE, process.pid)
                )
                for process in self.processes
                if process.pid in visible
            )
        return tree_rows(self.processes, self._children, visible, folded)

    def section_rows(
        self,
        *,
        annotations: Mapping[str, Annotation],
        folded: frozenset[str] = frozenset(),
        view_filter: str = ALL,
    ) -> tuple[Row, ...]:
        visible = self._visible_pids(
            annotations=annotations,
            query="",
            view_filter=view_filter,
        )
        groups: dict[Section, list[ProcessInfo]] = {}
        for process in self.processes:
            if process.pid not in visible:
                continue
            section = section_for(
                process,
                annotations.get(process.signature),
                self.parent_annotation(process, annotations),
                typed=self.typed(process, annotations),
                agent_shell=self.agent_shell(process, annotations),
                vouched=self.vouched(process, annotations),
            )
            groups.setdefault(section, []).append(process)
        rows: list[Row] = []
        for section in SECTION_ORDER:
            members = groups.get(section, [])
            if not members:
                continue
            header = SectionHeader.build(section, members, folded)
            rows.append(header)
            if header.folded:
                continue
            if section is Section.SAFE:
                rows.extend(
                    safe_band_rows(
                        members,
                        annotations,
                        folded,
                        processes=self.processes,
                        children=self._children,
                        by_pid=self._by_pid,
                    )
                )
                continue
            rows.extend(
                section_tree(
                    self.processes,
                    self._children,
                    members,
                    folded,
                    with_ancestors=True,
                    by_pid=self._by_pid,
                    scope=header.key,
                )
            )
        return tuple(rows)

    def default_folded(self) -> frozenset[str]:
        return default_folded(self.processes)

    def unreviewed(
        self,
        process: ProcessInfo,
        annotations: Mapping[str, Annotation],
    ) -> bool:
        if process.signature in annotations:
            return False
        if is_kernel_thread(process) or is_zombie(process):
            return False
        if self.agent_shell(process, annotations):
            return False
        parent = self.parent_annotation(process, annotations)
        return parent is None or not parent.covers(process.name)

    def agent_shell(
        self,
        process: ProcessInfo,
        annotations: Mapping[str, Annotation],
    ) -> bool:
        parent = self._by_pid.get(process.ppid)
        return (
            process.name in SHELLS
            and parent is not None
            and self._is_agent(parent, annotations)
        )

    def _is_agent(
        self,
        process: ProcessInfo,
        annotations: Mapping[str, Annotation],
    ) -> bool:
        own = annotations.get(process.signature)
        if own is not None:
            return own.agent
        parent = self.parent_annotation(process, annotations)
        return parent is not None and process.name in parent.agents

    def typed(
        self,
        process: ProcessInfo,
        annotations: Mapping[str, Annotation],
    ) -> bool:
        parent = self._by_pid.get(process.ppid)
        if parent is None:
            return False
        return typed_in_terminal(parent, self.parent_annotation(parent, annotations))

    def parent_annotation(
        self,
        process: ProcessInfo,
        annotations: Mapping[str, Annotation],
    ) -> Annotation | None:
        parent = self._by_pid.get(process.ppid)
        own = annotations.get(parent.signature) if parent else None
        return own.as_parent_of(parent.cmdline) if own and parent else None

    def parent_of(self, process: ProcessInfo) -> ProcessInfo | None:
        return self._by_pid.get(process.ppid)

    def vouched(
        self,
        process: ProcessInfo,
        annotations: Mapping[str, Annotation],
    ) -> bool:
        return vouched(self, process, annotations)

    def parent_chain(self, process: ProcessInfo) -> tuple[ProcessInfo, ...]:
        chain: list[ProcessInfo] = []
        seen: set[int] = set()
        current: ProcessInfo | None = process
        while current is not None and current.pid not in seen:
            chain.append(current)
            seen.add(current.pid)
            current = self._by_pid.get(current.ppid)
        return tuple(reversed(chain))

    def _visible_pids(
        self,
        *,
        annotations: Mapping[str, Annotation],
        query: str,
        view_filter: str,
    ) -> set[int]:
        visible = (
            matching_pids(self.processes, query)
            if query.strip()
            else {process.pid for process in self.processes}
        )
        if view_filter == UNREVIEWED:
            visible &= {
                process.pid
                for process in self.processes
                if self.unreviewed(process, annotations)
            }
        if view_filter == NETWORK:
            visible &= {process.pid for process in self.processes if process.listens}
        for pid in tuple(visible):
            add_ancestors(pid, visible, self._by_pid)
        return visible
