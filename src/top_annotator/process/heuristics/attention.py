from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from ...core.process_info import ProcessInfo

ATTENTION_PATH = Path(__file__).with_name("attention.yaml")


@dataclass(frozen=True, slots=True)
class AttentionConfig:
    """Programs that may be legitimate but always deserve a look while they
    run: what they do is in their arguments, or they hand root to the user."""

    argument_bound: frozenset[str]
    shells: frozenset[str]
    inline_interpreters: frozenset[str]
    inline_flags: frozenset[str]
    root_sockets: dict[str, tuple[str, ...]]
    x11_servers: frozenset[str]

    @classmethod
    def load(cls, path: Path = ATTENTION_PATH) -> AttentionConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        sockets = payload.get("root_sockets", {})
        return cls(
            argument_bound=frozenset(payload.get("argument_bound", ())),
            shells=frozenset(payload.get("shells", ())),
            inline_interpreters=frozenset(payload.get("inline_interpreters", ())),
            inline_flags=frozenset(payload.get("inline_flags", ())),
            root_sockets={
                str(daemon): tuple(str(path) for path in paths)
                for daemon, paths in sockets.items()
            },
            x11_servers=frozenset(payload.get("x11_servers", ())),
        )

    def reason(self, process: ProcessInfo) -> str | None:
        return self._argument_reason(process) or self._danger_reason(process)

    def _argument_reason(self, process: ProcessInfo) -> str | None:
        program = Path(process.exe or process.name).name
        if process.name in self.argument_bound or program in self.argument_bound:
            return f"{process.name} acts through its arguments: read them"
        code = self._inline_code(process)
        if code is None:
            return None
        first_word = Path(code.split()[0]).name if code.split() else ""
        if first_word in self.argument_bound:
            return f"a shell running {first_word}, which acts through its arguments"
        if process.name not in self.shells:
            return "inline code given on the command line: read it"
        return None

    def _inline_code(self, process: ProcessInfo) -> str | None:
        interpreters = self.shells | self.inline_interpreters
        if not {process.name, _unversioned(process)} & interpreters:
            return None
        arguments = process.cmdline[1:]
        for index, argument in enumerate(arguments):
            if argument in self.inline_flags:
                return arguments[index + 1] if index + 1 < len(arguments) else ""
        return None

    def _danger_reason(self, process: ProcessInfo) -> str | None:
        if process.name in self.x11_servers:
            return (
                "an X11 server: every graphical app can read your keys, the sudo"
                " password included, and inject others"
            )
        if process.user != "root":
            return None
        for socket in self.root_sockets.get(process.name, ()):
            if os.access(socket, os.W_OK):
                return (
                    f"privilege escalation: a root daemon whose socket {socket} you"
                    " can write; any program running as you can become root"
                    " through it"
                )
        return None


def _unversioned(process: ProcessInfo) -> str:
    """`python3.14` is `python`: a versioned interpreter is still one."""
    return Path(process.exe or process.name).name.rstrip(".0123456789")


ATTENTION = AttentionConfig.load()


def attention_reason(process: ProcessInfo) -> str | None:
    return ATTENTION.reason(process)
