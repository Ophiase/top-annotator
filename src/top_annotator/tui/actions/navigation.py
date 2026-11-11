from __future__ import annotations

from typing import Any

from ...core.section_header import SectionHeader
from ...core.tree import ProcessRow
from ..table import ProcessTable


class NavigationActions:
    def action_cursor_down(self: Any) -> None:
        self._move_cursor(1)

    def action_cursor_up(self: Any) -> None:
        self._move_cursor(-1)

    def _move_cursor(self: Any, step: int) -> None:
        candidate = self.query_one(ProcessTable).cursor_row + step
        if 0 <= candidate < len(self._rows):
            self.query_one(ProcessTable).move_cursor(row=candidate)

    def action_cursor_top(self: Any) -> None:
        if self._rows:
            self.query_one(ProcessTable).move_cursor(row=0)

    def action_cursor_bottom(self: Any) -> None:
        if self._rows:
            self.query_one(ProcessTable).move_cursor(row=len(self._rows) - 1)

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
