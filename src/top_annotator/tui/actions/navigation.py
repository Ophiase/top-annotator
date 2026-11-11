from __future__ import annotations

from typing import Any

from rich.style import Style

from ...core import ProcessInfo
from ...core.section_header import SectionHeader
from ...core.tree import ProcessRow
from ..table import ProcessTable

SELECTION_STYLE = Style(bgcolor="#f2c14e", color="#2b2416", bold=True)


class NavigationActions:
    _visual_anchor: int | None = None
    _picked: frozenset[str] = frozenset()

    def action_cursor_down(self: Any) -> None:
        self._move_cursor(1)

    def action_cursor_up(self: Any) -> None:
        self._move_cursor(-1)

    def _move_cursor(self: Any, step: int) -> None:
        candidate = self.query_one(ProcessTable).cursor_row + step
        if 0 <= candidate < len(self._rows):
            self.query_one(ProcessTable).move_cursor(row=candidate)
            self._paint_selection()

    def action_cursor_top(self: Any) -> None:
        if self._rows:
            self.query_one(ProcessTable).move_cursor(row=0)
            self._paint_selection()

    def action_cursor_bottom(self: Any) -> None:
        if self._rows:
            self.query_one(ProcessTable).move_cursor(row=len(self._rows) - 1)
            self._paint_selection()

    def action_toggle_visual(self: Any) -> None:
        if self._visual_anchor is not None:
            self._commit_zone()
        else:
            self._visual_anchor = self.query_one(ProcessTable).cursor_row
            self.notify(
                "visual: j/k extend · Esc keeps the zone, Esc again clears all"
                " · v starts another · s S a x A apply",
                timeout=4,
            )
        self._paint_selection()

    def _commit_zone(self: Any) -> None:
        zone = {self._rows[index].key for index in self._zone()}
        self._picked = frozenset(self._picked | zone)
        self._visual_anchor = None

    def _escape_selection(self: Any) -> bool:
        """The first Esc ends the zone being drawn and keeps it; the next one
        drops the whole selection. False when there was nothing to drop."""
        if self._visual_anchor is not None:
            self._commit_zone()
        elif self._picked:
            self._picked = frozenset()
        else:
            return False
        self._paint_selection()
        return True

    def _clear_selection(self: Any) -> None:
        self._visual_anchor = None
        self._picked = frozenset()
        self._paint_selection()

    def _zone(self: Any) -> range:
        if self._visual_anchor is None:
            return range(0)
        cursor = self.query_one(ProcessTable).cursor_row
        low, high = sorted((self._visual_anchor, cursor))
        return range(max(low, 0), min(high, len(self._rows) - 1) + 1)

    def _selected_indices(self: Any) -> set[int]:
        picked = {
            index for index, row in enumerate(self._rows) if row.key in self._picked
        }
        return picked | set(self._zone())

    def _paint_selection(self: Any) -> None:
        """Repaint only the rows whose selection changed: a full refresh on
        every cursor move makes the table flicker."""
        table = self.query_one(ProcessTable)
        before = set(table.selection_styles)
        table.selection_styles = dict.fromkeys(
            self._selected_indices(), SELECTION_STYLE
        )
        changed = before ^ set(table.selection_styles)
        if changed:
            table.clear_render_cache()
            for index in changed:
                if index < table.row_count:
                    table.refresh_row(index)
        if changed or before:
            self._update_status()

    def _targets(self: Any) -> tuple[ProcessInfo, ...]:
        """The processes an action applies to: the selection, or the process
        under the cursor; one per signature. A selection skips the dim parents
        shown as context, which only the cursor can aim at."""
        selected = sorted(self._selected_indices())
        indices = selected or [self.query_one(ProcessTable).cursor_row]
        chosen: dict[str, ProcessInfo] = {}
        for index in indices:
            row = self._rows[index] if 0 <= index < len(self._rows) else None
            if not isinstance(row, ProcessRow) or (row.is_context and selected):
                continue
            chosen.setdefault(row.process.signature, row.process)
        return tuple(chosen.values())

    def _header_members(self: Any) -> tuple[ProcessInfo, ...]:
        index = self.query_one(ProcessTable).cursor_row
        row = self._rows[index] if 0 <= index < len(self._rows) else None
        if not isinstance(row, SectionHeader) or self._tree is None:
            return ()
        pids = set(row.pids)
        return tuple(process for process in self._tree.processes if process.pid in pids)

    def _current_row(self: Any) -> ProcessRow | None:
        index = self.query_one(ProcessTable).cursor_row
        if 0 <= index < len(self._rows):
            row = self._rows[index]
            if isinstance(row, ProcessRow):
                return row
        return None

    def _foldable_key(self: Any) -> str | None:
        """A band, a provider group, or a process with children."""
        index = self.query_one(ProcessTable).cursor_row
        if not 0 <= index < len(self._rows):
            return None
        row = self._rows[index]
        if isinstance(row, SectionHeader) or row.has_children:
            return row.key
        return None

    def action_toggle_fold(self: Any) -> None:
        key = self._foldable_key()
        if key is not None:
            self._folded.symmetric_difference_update({key})
            self._render()

    def action_fold(self: Any) -> None:
        key = self._foldable_key()
        if key is not None:
            self._folded.add(key)
            self._render()

    def action_unfold(self: Any) -> None:
        key = self._foldable_key()
        if key is not None:
            self._folded.discard(key)
            self._render()
