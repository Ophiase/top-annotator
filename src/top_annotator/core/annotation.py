from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date

from .category import Category

SHELLS = frozenset({"bash", "dash", "fish", "sh", "zsh"})
FLAGS: dict[str, str] = {
    "exclusive": "any child not listed in its children goes WEIRD",
    "gui": "a desktop application the user drives",
    "terminal": "a terminal the user types into; covers its shells",
    "interactive": "expected only when typed in a user terminal; WEIRD elsewhere",
    "agent": "an AI agent: its shells run its commands",
}


@dataclass(frozen=True, slots=True)
class Annotation:
    category: Category
    note: str = ""
    provider: str = ""
    updated: date = field(default_factory=date.today)
    children: tuple[str, ...] | None = None
    exclusive: bool = False
    gui: bool = False
    terminal: bool = False
    interactive: bool = False
    agent: bool = False
    agents: tuple[str, ...] = ()
    plugin_args: tuple[str, ...] = ()

    def plugin_host(self, cmdline: tuple[str, ...]) -> bool:
        """A process of this program that runs third-party plugins, told by its argv."""
        return any(argument in self.plugin_args for argument in cmdline)

    def as_parent_of(self, cmdline: tuple[str, ...]) -> Annotation:
        """What this entry vouches for when the parent runs with `cmdline`:
        a plugin host is no terminal, its shells come from a plugin."""
        if self.terminal and self.plugin_host(cmdline):
            return replace(self, terminal=False)
        return self

    def covers(self, name: str) -> bool:
        if self.terminal and name in SHELLS:
            return True
        if name in self.agents:
            return True
        return self.children is not None and name in self.children

    def flags(self) -> dict[str, bool]:
        return {flag: getattr(self, flag) for flag in FLAGS}

    def forbids(self, name: str) -> bool:
        return self.exclusive and not self.covers(name)
