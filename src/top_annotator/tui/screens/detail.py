from __future__ import annotations

from typing import ClassVar

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static

from ...core import PROVIDERS, Annotation, ProcessInfo, provider_of, section_reason
from ...process.verify import PackageIntegrity
from ..presentation import CATEGORY_COLORS, human_bytes


class DetailScreen(ModalScreen[None]):
    CSS = """
    DetailScreen { align: center middle; }
    #detail-dialog {
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
        process: ProcessInfo,
        annotation: Annotation | None,
        chain: tuple[ProcessInfo, ...],
        parent: Annotation | None,
        typed: bool,
        integrity: PackageIntegrity | None = None,
        history: str = "",
        suggestion: Annotation | None = None,
    ) -> None:
        super().__init__()
        self._process = process
        self._annotation = annotation
        self._chain = chain
        self._parent_annotation = parent
        self._typed = typed
        self._integrity = integrity
        self._history = history
        self._suggestion = suggestion if annotation is None else None

    def compose(self) -> ComposeResult:
        yield Static(self._content(), id="detail-dialog")

    def _content(self) -> str:
        process = self._process
        category = self._annotation.category if self._annotation else None
        color = CATEGORY_COLORS.get(category, "bold bright_red")
        label = category.value.upper() if category else "NEW — not audited"
        note = escape(self._annotation.note) if self._annotation else ""
        chain = " → ".join(
            f"{escape(ancestor.name)}[{ancestor.pid}]" for ancestor in self._chain
        )
        reason = section_reason(
            process,
            self._annotation,
            self._parent_annotation,
            typed=self._typed,
        )
        weird = f"[dim]weird[/dim]      {escape(reason)}\n" if reason else ""
        if not process.exe and process.cmdline:
            weird += (
                "[dim]identity[/dim]   from argv[0], which the process chose:"
                " `sudo top-annotator snapshot` reads the real executable\n"
            )
        if self._suggestion is not None:
            weird += (
                f"[dim]suggests[/dim]   {self._suggestion.category.value}"
                f" — {escape(self._suggestion.note)}  [dim](A accepts)[/dim]\n"
            )
        if self._history:
            weird += f"[dim]history[/dim]    {escape(self._history)}\n"
        integrity = ""
        if self._integrity is not None:
            integrity = f"[dim]origin[/dim]     {escape(self._integrity.summary)}\n"
            detail = self._integrity.detail()
            if detail:
                integrity += f"[dim]diff[/dim]       {escape(detail)}\n"
        return (
            f"[bold]PID {process.pid}[/bold]  ·  state {escape(process.state)}"
            f"  ·  {process.threads} threads\n"
            f"[{color}]{label}[/{color}]\n"
            f"[dim]signature[/dim]  {escape(process.signature)}\n"
            f"[dim]exe[/dim]        {escape(process.exe or '—')}\n"
            f"[dim]user[/dim]       {escape(process.user)}\n"
            f"[dim]memory[/dim]     {human_bytes(process.rss_bytes)}"
            f"  ·  [dim]cpu[/dim] {process.cpu_percent:.1f}%\n"
            f"[dim]command[/dim]    {escape(process.command)}\n"
            f"[dim]parents[/dim]    {chain}\n"
            f"{_service_lines(process, self._annotation)}"
            f"{weird}{integrity}" + (f"\n[dim]note[/dim] {note}" if note else "")
        )

    def action_close(self) -> None:
        self.dismiss(None)


def _service_lines(process: ProcessInfo, annotation: Annotation | None) -> str:
    lines = ""
    provider = provider_of(process, annotation)
    if provider:
        lines += f"[dim]from[/dim]       {escape(PROVIDERS.get(provider, provider))}\n"
    if process.service:
        lines += f"[dim]service[/dim]    {escape(process.unit)}\n"
    if process.listens:
        lines += f"[dim]listens[/dim]    {escape(', '.join(process.listens))}\n"
    if annotation is not None and annotation.children is not None:
        expected = ", ".join(annotation.children) or "none"
        lines += f"[dim]children[/dim]   {escape(expected)}\n"
    return lines
