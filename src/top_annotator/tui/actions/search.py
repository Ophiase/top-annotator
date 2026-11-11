from __future__ import annotations

from typing import Any

from textual.widgets import Input

from ..table import ProcessTable

SEARCH_ID = "search"


class SearchActions:
    """Named `on_input_*` handlers: Textual's `@on` is not collected from a mixin."""

    def action_focus_search(self: Any) -> None:
        self.query_one(Input).focus()

    def on_input_changed(self: Any, event: Input.Changed) -> None:
        if event.input.id != SEARCH_ID:
            return
        self._query = event.value
        self._render()

    def on_input_submitted(self: Any, event: Input.Submitted) -> None:
        if event.input.id != SEARCH_ID:
            return
        event.stop()
        self.query_one(ProcessTable).focus()

    def action_escape(self: Any) -> None:
        search = self.query_one(Input)
        if search.has_focus or self._query:
            search.value = ""
            self._query = ""
            self.query_one(ProcessTable).focus()
            self._render()
