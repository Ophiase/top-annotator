from __future__ import annotations

from collections import Counter
from typing import ClassVar

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static

from ...core import Annotation, ProcessInfo, SectionHeader
from ..presentation import human_bytes

TOP = 8


class GroupScreen(ModalScreen[None]):
    """What a band or provider group holds, opened with Enter on its header."""

    CSS = """
    GroupScreen { align: center middle; }
    #group-dialog {
        width: 85%; height: auto; max-height: 90%; padding: 1 2;
        border: round $primary; background: $surface; overflow-y: auto;
    }
    """

    BINDINGS: ClassVar = [
        Binding("escape", "close", "Close", show=False),
        Binding("enter", "close", "Close", show=False),
        Binding("q", "close", "Close", show=False),
    ]

    def __init__(
        self,
        header: SectionHeader,
        meaning: str,
        members: tuple[ProcessInfo, ...],
        annotations: dict[str, Annotation],
    ) -> None:
        super().__init__()
        self._header = header
        self._meaning = meaning
        self._members = members
        self._annotations = annotations

    def compose(self) -> ComposeResult:
        yield Static(self._content(), id="group-dialog")

    def _content(self) -> str:
        header = self._header
        levels = Counter(
            annotation.category.value if annotation else "covered by its parent"
            for annotation in (
                self._annotations.get(process.signature) for process in self._members
            )
        )
        heaviest = sorted(self._members, key=lambda process: -process.rss_bytes)
        lines = [
            f"[bold]{escape(header.key)}[/bold]  ·  {escape(self._meaning)}",
            f"[dim]holds[/dim]      {header.count} processes  ·  "
            f"{human_bytes(header.rss_bytes)}  ·  {header.cpu_percent:.1f}% cpu",
        ]
        if header.parents:
            chain = " ∈ ".join(header.parents)
            lines.append(f"[dim]under[/dim]      {escape(chain)}  (shared by all)")
        lines.append(
            "[dim]trust[/dim]      "
            + escape(
                ", ".join(f"{level} {count}" for level, count in levels.most_common())
            )
        )
        lines.append("[dim]heaviest[/dim]")
        lines.extend(
            f"  {human_bytes(process.rss_bytes):>8}  {escape(process.name)}"
            f"[dim] [{process.pid}][/dim]"
            for process in heaviest[:TOP]
        )
        return "\n".join(lines)

    def action_close(self) -> None:
        self.dismiss(None)
