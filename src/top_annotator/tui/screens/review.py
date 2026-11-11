from __future__ import annotations

from typing import ClassVar

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.fuzzy import Matcher
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Static

from ...audit import RuleRow
from ..presentation import CATEGORY_COLORS


class ReviewScreen(ModalScreen[None]):
    CSS = """
    ReviewScreen { align: center middle; }
    #review-dialog {
        width: 90%; height: 85%; padding: 1 2;
        border: round $primary; background: $surface;
    }
    #review-rules { height: 1fr; }
    """

    BINDINGS: ClassVar = [
        Binding("escape", "close", "Close", show=False),
        Binding("down", "focus_rules", "Rules", show=False),
    ]

    def __init__(self, rows: tuple[RuleRow, ...]) -> None:
        super().__init__()
        self._rows = rows

    def compose(self) -> ComposeResult:
        with Vertical(id="review-dialog"):
            yield Static("[bold]Rules review[/bold]  ·  last changed first\n")
            yield Input(placeholder="fuzzy search: signature, note, trust, source")
            yield DataTable(id="review-rules")
            yield Static("[dim]type to filter · ↓ rules · esc close[/dim]")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("changed", "source", "trust", "signature", "note")
        self._fill("")
        self.query_one(Input).focus()

    @on(Input.Changed)
    def search(self, event: Input.Changed) -> None:
        self._fill(event.value)

    def _fill(self, query: str) -> None:
        table = self.query_one(DataTable)
        table.clear()
        matcher = Matcher(query.strip()) if query.strip() else None
        for row in self._rows:
            label = f"{row.signature} {row.note} {row.category.value} {row.source}"
            if matcher is not None and matcher.match(label) <= 0:
                continue
            table.add_row(
                Text(row.changed.replace("T", " "), style="dim"),
                Text(row.source, style="bold" if row.source == "session" else "dim"),
                Text(row.category.value.upper(), style=CATEGORY_COLORS[row.category]),
                Text(row.signature),
                Text(row.note, style="dim"),
            )

    def action_focus_rules(self) -> None:
        self.query_one(DataTable).focus()

    def action_close(self) -> None:
        self.dismiss(None)
