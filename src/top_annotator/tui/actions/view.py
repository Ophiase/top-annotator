from __future__ import annotations

import shutil
import subprocess
from typing import Any

from textual.timer import Timer

from ...core import ProcessInfo, provider_of
from ...core.tree.filters import FILTERS
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
