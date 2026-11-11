from __future__ import annotations

import shutil
import subprocess
from typing import Any

from textual.timer import Timer
from textual.widgets import Static

from ...audit import BASE_AUDIT
from ...core import Category, ProcessInfo, provider_of
from ...core.tree import ProcessRow
from ...core.tree.filters import ALL, FILTERS
from ...process.cache import shown_path
from ..screens import ChoiceScreen
from ..table import ProcessTable

FILTER_LABELS = {
    name: f"{name.upper()} — {meaning}" for name, meaning in FILTERS.items()
}


class ViewActions:
    _refresh_timer: Timer | None

    def action_choose_filter(self: Any) -> None:
        self.push_screen(
            ChoiceScreen("Show", FILTER_LABELS, self._filter),
            self._set_filter,
        )

    def _set_filter(self: Any, choice: str | None) -> None:
        self.query_one(ProcessTable).focus()
        if choice is not None:
            self._filter = choice
            self._render()

    def action_yank(self: Any) -> None:
        process = self._selected_process()
        if process is None or self._tree is None:
            return
        block = self._yank_block(process)
        copied = copy_with_wl(block)
        if not copied:
            self.copy_to_clipboard(block)
        tool = "wl-copy" if copied else "terminal (OSC 52)"
        self.notify(f"copied {process.name}[{process.pid}] via {tool}", timeout=1.5)

    def _yank_block(self: Any, process: ProcessInfo) -> str:
        annotation = self._store.annotation_for(process.signature)
        trust = annotation.category.value if annotation else "unannotated"
        provider = provider_of(process, annotation) or "?"
        chain = " → ".join(
            f"{ancestor.name}[{ancestor.pid}]"
            for ancestor in self._tree.parent_chain(process)
        )
        return "\n".join((
            f"signature  {process.signature}",
            f"pid        {process.pid} (ppid {process.ppid}, {process.user}, "
            f"state {process.state})",
            f"exe        {process.exe or '—'}",
            f"command    {process.command}",
            f"parents    {chain}",
            f"audit      {trust} · from {provider} · "
            f"source {self._store.source_for(process.signature) or '—'}",
        ))

    def action_cycle_view(self: Any) -> None:
        self._view = {
            "sections": "tree",
            "tree": "flat",
            "flat": "sections",
        }[self._view]
        self._render()

    @property
    def frozen(self: Any) -> bool:
        return self._frozen

    def action_toggle_freeze(self: Any) -> None:
        self._frozen = not self._frozen
        if self._refresh_timer is not None:
            if self._frozen:
                self._refresh_timer.pause()
            else:
                self._refresh_timer.resume()
        self._update_status()
        label = "frozen" if self._frozen else "resumed"
        self.notify(f"refresh {label}", timeout=1.5)

    def action_refresh_now(self: Any) -> None:
        self._scan()

    async def action_quit(self: Any) -> None:
        self.exit()

    def _suggested_level(self: Any, process: ProcessInfo) -> str:
        suggestion = self._store.suggestions.get(process.signature)
        return suggestion.category.value if suggestion else ""

    def _update_status(self: Any) -> None:
        processes = self._tree.processes if self._tree else ()
        unreviewed = sum(
            1
            for process in processes
            if self._tree is not None
            and self._tree.unreviewed(process, self._store.annotations)
        )
        safe = sum(
            1
            for annotation in self._store.annotations.values()
            if annotation.category is Category.SAFE
        )
        suggested = len({
            process.signature
            for process in processes
            if self._suggested_level(process)
            and process.signature not in self._store.annotations
        })
        offer = (
            f"  ·  [#7b5e1f]{suggested} suggested: A accepts, on a header all[/]"
            if suggested
            else ""
        )
        flags = [self._view, f"audit {self._audit_label()}"]
        if self._notice:
            flags = [self._view, "demo data, discarded on exit"]
        elif self._store.session_path is not None:
            flags.append(f"yours {shown_path(self._store.session_path)}")
        if self._selected_indices():
            mode = "VISUAL" if self._visual_anchor is not None else "SELECTED"
            selected = len(self._targets())
            flags.insert(0, f"[b #2b2416 on #f2c14e] {mode} {selected} [/]")
        if self._frozen:
            flags.append("frozen")
        if self._filter != ALL:
            flags.append(f"filter {self._filter}")
        if self._query:
            flags.append("search")
        shown = sum(1 for row in self._rows if isinstance(row, ProcessRow))
        query = f"  ·  {self._query}" if self._query else ""
        mode = f"  ·  {', '.join(flags)}" if flags else ""
        self.query_one("#status", Static).update(
            f"[bold]{shown}[/bold]/{len(processes)} shown"
            f"  ·  [bold bright_red]{unreviewed}[/bold bright_red] unreviewed"
            f"  ·  [green]{safe}[/green] safe{offer}"
            "  ·  [dim]s trust · S level · a cycle · x clear · n note"
            " · f filter · t sections/tree/flat[/dim]"
            f"{mode}{query}"
        )

    def _audit_label(self: Any) -> str:
        root = self._store.root
        label = "bundled" if root == BASE_AUDIT.resolve() else shown_path(root)
        read = [scope for scope in self._store.scopes if (root / scope).is_dir()]
        return f"{label}: {', '.join(read)}" if read else label


def copy_with_wl(text: str) -> bool:
    """Wayland's clipboard; False when wl-copy is missing or fails, so the
    caller can fall back to the terminal's OSC 52."""
    executable = shutil.which("wl-copy")
    if executable is None:
        return False
    try:
        result = subprocess.run(
            [executable],
            input=text,
            text=True,
            timeout=2,
            check=False,
            capture_output=True,
        )
    except OSError, subprocess.TimeoutExpired:
        return False
    return result.returncode == 0
