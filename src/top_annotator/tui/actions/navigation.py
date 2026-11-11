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
        cursor = self.query_one(ProcessTable).cursor_row
        self._visual_anchor = None if self._visual_anchor is not None else cursor
        self._paint_selection()
        if self._visual_anchor is not None:
            self.notify(
                "visual: j/k extend · s S a x A apply · v or Esc leave", timeout=3
            )

    def _leave_visual(self: Any) -> bool:
        was_visual = self._visual_anchor is not None
        self._visual_anchor = None
        self._paint_selection()
        return was_visual

    def _selection(self: Any) -> range:
        cursor = self.query_one(ProcessTable).cursor_row
        if self._visual_anchor is None:
            return range(cursor, cursor + 1)
        low, high = sorted((self._visual_anchor, cursor))
        return range(low, high + 1)

    def _paint_selection(self: Any) -> None:
        """Repaint only the rows whose selection changed: a full refresh on
        every cursor move makes the table flicker."""
        table = self.query_one(ProcessTable)
        before = set(table.selection_styles)
        table.selection_styles = (
            dict.fromkeys(self._selection(), SELECTION_STYLE)
            if self._visual_anchor is not None
            else {}
        )
        changed = before ^ set(table.selection_styles)
        if changed:
            table.clear_render_cache()
            for index in changed:
                table.refresh_row(index)
        if changed or before:
            self._update_status()

    def _targets(self: Any) -> tuple[ProcessInfo, ...]:
        """The processes an action applies to: the visual selection, or the
        process under the cursor; one per signature. A selection skips the
        dim parents shown as context, which only the cursor can aim at."""
        chosen: dict[str, ProcessInfo] = {}
        visual = self._visual_anchor is not None
        for index in self._selection():
            row = self._rows[index] if 0 <= index < len(self._rows) else None
            context = row.is_context if isinstance(row, ProcessRow) else False
            if isinstance(row, ProcessRow) and not (context and visual):
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
