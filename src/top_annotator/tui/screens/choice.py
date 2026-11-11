from __future__ import annotations

from typing import ClassVar

from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option


class ChoiceScreen(ModalScreen[str | None]):
    """Pick one option by id: the trust level picker, the filter menu."""

    CSS = """
    ChoiceScreen { align: center middle; }
    #choice-dialog {
        width: 70%; height: auto; max-height: 80%; padding: 1 2;
        border: round $primary; background: $surface;
    }
    """

    BINDINGS: ClassVar = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        title: str,
        choices: dict[str, str],
        current: str | None = None,
    ) -> None:
        super().__init__()
        self._title = title
        self._choices = choices
        self._current = current

    def compose(self) -> ComposeResult:
        with Vertical(id="choice-dialog"):
            yield Static(f"[bold]{escape(self._title)}[/bold]\n")
            yield OptionList(
                *[Option(label, id=key) for key, label in self._choices.items()],
                id="choice-options",
            )
            yield Static("[dim]enter choose · esc cancel[/dim]")

    def on_mount(self) -> None:
        options = self.query_one(OptionList)
        keys = list(self._choices)
        if self._current in keys:
            options.highlighted = keys.index(self._current)
        options.focus()

    @on(OptionList.OptionSelected, "#choice-options")
    def choose(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        self.dismiss(event.option.id)

    def action_cancel(self) -> None:
        self.dismiss(None)
