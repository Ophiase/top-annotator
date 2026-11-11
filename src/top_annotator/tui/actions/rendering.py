from __future__ import annotations

from typing import Any

from rich.text import Text

from ...core import ProcessInfo
from ...core.section_header import SectionHeader
from ...core.tree import ProcessRow, Row
from ...core.tree.process_tree import ProcessTree
from ..presentation import (
    CATEGORY_COLORS,
    PROVIDER_COLORS,
    audit_cell,
    group_meaning,
    group_title,
    header_style,
    human_bytes,
    kind_cell,
    net_cell,
    provider_cell,
    short,
)
from ..table import ProcessTable


class RenderingActions:
    _tree: ProcessTree | None
    _rows: tuple[Row, ...]
    _query: str
    _folded: set[str]
    _filter: str
    _view: str
    _frozen: bool
    _store: Any

    def _render(self: Any, selected_pid: int | None = None) -> None:
        selected_key = self._selected_key() if selected_pid is None else ""
        if selected_pid is None:
            selected_pid = self._selected_pid()
        if self._tree is None:
            return
        self._rows = self._rows_for_view()
        table = self.query_one(ProcessTable)
        scroll_y = table.scroll_offset.y
        with self.app.batch_update():
            table.clear()
            table.row_styles = {
                index: header_style(row)
                for index, row in enumerate(self._rows)
                if isinstance(row, SectionHeader)
            }
            for index, row in enumerate(self._rows):
                if isinstance(row, SectionHeader):
                    table.add_row(*self._header_cells(row), key=f"header-{row.key}")
                else:
                    table.add_row(*self._cells(row), key=f"row-{index}")
            self._restore_cursor(selected_pid, selected_key)
            self._update_status()
        self.call_after_refresh(
            lambda: table.scroll_to(y=scroll_y, animate=False, immediate=True)
        )

    def _rows_for_view(self: Any) -> tuple[Row, ...]:
        if self._tree is None:
            return ()
        if self._query:
            return self._tree.rows(
                annotations=self._store.annotations,
                query=self._query,
                folded=frozenset(self._folded),
                view_filter=self._filter,
                tree_view=True,
            )
        if self._view == "sections":
            return self._tree.section_rows(
                annotations=self._store.annotations,
                folded=frozenset(self._folded),
                view_filter=self._filter,
            )
        return self._tree.rows(
            annotations=self._store.annotations,
            folded=frozenset(self._folded),
            view_filter=self._filter,
            tree_view=self._view == "tree",
        )

    @staticmethod
    def _header_cells(header: SectionHeader) -> tuple[Text, ...]:
        marker = "▸" if header.folded else "▾"
        name = group_title(header)
        indent = "  " * (header.group.count("/") + 1) if header.group else ""
        style = PROVIDER_COLORS.get(header.group.split("/")[0], "")
        blank = [Text("") for _ in range(5)]
        label = Text(
            f"{indent}{marker} {name}  ({header.count})", style=f"bold {style}"
        )
        if "/" in header.group:
            label.append(f"  {group_meaning(header)}", style="dim")
        if header.parents:
            label.append(
                "".join(f" ∈ {parent}" for parent in header.parents), style="dim"
            )
        return (
            label,
            *blank,
            Text(human_bytes(header.rss_bytes), style="bold", justify="right"),
            Text(f"{header.cpu_percent:.1f}", style="bold", justify="right"),
            Text(""),
            Text(""),
        )

    def _cells(self: Any, row: ProcessRow) -> tuple[Text, ...]:
        process = row.process
        annotation = self._store.annotation_for(process.signature)
        parent = self._tree.parent_annotation(process, self._store.annotations)
        category = annotation.category if annotation else None
        name_style = CATEGORY_COLORS.get(category, "bold") if category else "bold"
        if row.is_context:
            name_style = f"dim {name_style}"
        return (
            Text(f"{row.prefix}{process.name}", style=name_style),
            Text(str(process.pid), style="dim"),
            audit_cell(
                annotation,
                process,
                parent,
                agent_shell=self._tree.agent_shell(process, self._store.annotations),
                suggested=self._suggested_level(process),
            ),
            provider_cell(process, annotation),
            net_cell(process),
            kind_cell(process, annotation),
            Text(human_bytes(process.rss_bytes), justify="right"),
            Text(f"{process.cpu_percent:.1f}", justify="right"),
            Text(process.user, style="dim"),
            Text(short(process.command, 90), style="dim"),
        )

    def _restore_cursor(self: Any, pid: int | None, key: str = "") -> None:
        if not self._rows:
            return
        by_key = (
            position
            for position, row in enumerate(self._rows)
            if key and row.key == key
        )
        by_pid = (
            position
            for position, row in enumerate(self._rows)
            if isinstance(row, ProcessRow) and row.process.pid == pid
        )
        index = next(by_key, next(by_pid, self._first_process_index()))
        self.query_one(ProcessTable).move_cursor(row=index, scroll=False)

    def _first_process_index(self: Any) -> int:
        return next(
            (
                position
                for position, row in enumerate(self._rows)
                if isinstance(row, ProcessRow)
            ),
            0,
        )

    def _selected_key(self: Any) -> str:
        index = self.query_one(ProcessTable).cursor_row
        return self._rows[index].key if 0 <= index < len(self._rows) else ""

    def _selected_pid(self: Any) -> int | None:
        index = self.query_one(ProcessTable).cursor_row
        if 0 <= index < len(self._rows):
            row = self._rows[index]
            if isinstance(row, ProcessRow):
                return row.process.pid
        return None

    def _selected_process(self: Any) -> ProcessInfo | None:
        pid = self._selected_pid()
        if pid is None or self._tree is None:
            return None
        return next(
            (process for process in self._tree.processes if process.pid == pid),
            None,
        )
