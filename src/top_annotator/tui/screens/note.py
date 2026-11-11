from __future__ import annotations

from typing import ClassVar

from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static


class NoteScreen(ModalScreen[str | None]):
    CSS = """
    NoteScreen { align: center middle; }
    #note-dialog {
        width: 70%; height: auto; padding: 1 2;
        border: round $primary; background: $surface;
    }
    """

    BINDINGS: ClassVar = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+s", "save", "Save", show=False),
    ]

    def __init__(self, signature: str, note: str) -> None:
        super().__init__()
        self._signature = signature
        self._note = note

    def compose(self) -> ComposeResult:
        with Vertical(id="note-dialog"):
            yield Static(f"[bold]{escape(self._signature)}[/bold]\n")
            yield Input(
                value=self._note,
                placeholder="why is this process safe, watchlisted, ...",
                id="note-input",
            )
            yield Static("[dim]enter save · esc cancel[/dim]")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    @on(Input.Submitted, "#note-input")
    def save_on_enter(self, event: Input.Submitted) -> None:
        event.stop()
        self.dismiss(event.value)

    def action_save(self) -> None:
        self.dismiss(self.query_one(Input).value)

    def action_cancel(self) -> None:
        self.dismiss(None)
