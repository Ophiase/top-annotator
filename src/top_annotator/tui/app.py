from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.timer import Timer
from textual.widgets import Footer, Input, Static

from ..audit import AuditStore
from ..core.tree import ProcessTree
from ..core.tree.filters import ALL
from ..process.scan import ProcessScanner, Scanner
from ..process.verify import VerificationCache
from .actions import (
    AnnotationActions,
    NavigationActions,
    RenderingActions,
    SearchActions,
    TopAnnotatorCommands,
    ViewActions,
)
from .table import ProcessTable
from .theme import PAPER_THEME


class TopAnnotatorApp(
    AnnotationActions,
    NavigationActions,
    RenderingActions,
    SearchActions,
    ViewActions,
    App[None],
):
    TITLE = "top-annotator"
    SUB_TITLE = "audit the unknown, ignore the rest"
    COMMANDS: ClassVar = App.COMMANDS | {TopAnnotatorCommands}
    CSS = """
    Screen { layout: vertical; background: $surface; }
    #search {
        height: 1; border: none; padding: 0 1;
        background: $boost; color: $text;
    }
    #search:focus { background: $primary-darken-2; }
    #processes { height: 1fr; }
    #status { height: 1; padding: 0 1; background: $panel; color: $text-muted; }
    """

    BINDINGS: ClassVar = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("g", "cursor_top", "Top", show=False),
        Binding("G", "cursor_bottom", "Bottom", show=False),
        Binding("space", "toggle_fold", "Fold", show=False),
        Binding("h", "fold", "Fold", show=False),
        Binding("l", "unfold", "Unfold", show=False),
        Binding("slash", "focus_search", "Search"),
        Binding("enter", "show_detail", "Info"),
        Binding("s", "mark_trust", "Trust"),
        Binding("S", "choose_trust", "Trust level"),
        Binding("a", "cycle_category", "Category"),
        Binding("A", "accept_suggestion", "Accept"),
        Binding("x", "clear_annotation", "Clear"),
        Binding("u", "undo", "Undo"),
        Binding("n", "edit_note", "Note"),
        Binding("y", "yank", "Yank"),
        Binding("f", "choose_filter", "Filter"),
        Binding("t", "cycle_view", "View"),
        Binding("R", "show_review", "Review", show=False),
        Binding("p", "toggle_freeze", "Freeze", show=False),
        Binding("r", "refresh_now", "Refresh", show=False),
        Binding("escape", "escape", "Esc", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        store: AuditStore,
        *,
        scanner: Scanner | None = None,
        refresh_seconds: float = 2.0,
        cache_dir: Path | None = None,
        notice: str = "",
    ) -> None:
        super().__init__()
        self._notice = notice
        if notice:
            self.sub_title = notice
        self.register_theme(PAPER_THEME)
        self.theme = PAPER_THEME.name
        self._store = store
        self._scanner = scanner or ProcessScanner()
        self._refresh_seconds = refresh_seconds
        self._verification_cache = (
            VerificationCache(cache_dir) if cache_dir is not None else None
        )
        self._tree: ProcessTree | None = None
        self._rows = ()
        self._query = ""
        self._folded: set[str] = set()
        self._filter = ALL
        self._view = "sections"
        self._frozen = True
        self._refresh_timer: Timer | None = None
        self._default_folds_applied = False

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="press / then type — fuzzy search, parent chain included",
            id="search",
        )
        yield ProcessTable(id="processes")
        yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(ProcessTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns(
            "process",
            "pid",
            "audit",
            "from",
            "net",
            "kind",
            "mem",
            "cpu%",
            "user",
            "command",
        )
        self._scan()
        self._refresh_timer = self.set_interval(self._refresh_seconds, self._scan)
        self._refresh_timer.pause()
        table.focus()

    def _scan(self) -> None:
        selected = self._selected_pid()
        processes = self._scanner.scan()
        self._tree = ProcessTree(processes)
        if not self._default_folds_applied:
            self._folded.update(self._tree.default_folded())
            self._default_folds_applied = True
        self._render(selected)
