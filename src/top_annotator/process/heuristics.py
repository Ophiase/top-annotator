from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from ..core.process_info import ProcessInfo

HEURISTICS_PATH = Path(__file__).with_name("heuristics.yaml")


@dataclass(frozen=True, slots=True)
class HeuristicsConfig:
    system_directories: tuple[str, ...]
    suspicious_directories: tuple[str, ...]
    system_executables: frozenset[str]
    name_aliases: dict[str, frozenset[str]]
    system_name_prefixes: tuple[str, ...]
    kernel_thread_parent_pids: frozenset[int]

    @classmethod
    def load(cls, path: Path = HEURISTICS_PATH) -> HeuristicsConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a mapping")
        aliases = payload.get("name_aliases", {})
        if not isinstance(aliases, dict):
            raise ValueError("name_aliases must be a mapping")
        return cls(
            system_directories=_string_tuple(payload, "system_directories"),
            suspicious_directories=_string_tuple(payload, "suspicious_directories"),
            system_executables=frozenset(_string_tuple(payload, "system_executables")),
            name_aliases={
                str(name): frozenset(_string_list(alias, "name_aliases"))
                for name, alias in aliases.items()
            },
            system_name_prefixes=_string_tuple(payload, "system_name_prefixes"),
            kernel_thread_parent_pids=frozenset(
                _int_tuple(payload, "kernel_thread_parent_pids")
            ),
        )


def _string_list(value: object, key: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return tuple(value)


def _string_tuple(payload: dict[str, object], key: str) -> tuple[str, ...]:
    return _string_list(payload.get(key, []), key)


def _int_tuple(payload: dict[str, object], key: str) -> tuple[int, ...]:
    value = payload.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    ):
        raise ValueError(f"{key} must be a list of integers")
    return tuple(value)


CONFIG = HeuristicsConfig.load()
SYSTEM_DIRECTORIES = CONFIG.system_directories
SUSPICIOUS_DIRECTORIES = CONFIG.suspicious_directories
SYSTEM_EXECUTABLES = CONFIG.system_executables
NAME_ALIASES = CONFIG.name_aliases
SYSTEM_NAME_PREFIXES = CONFIG.system_name_prefixes


def is_kernel_thread(process: ProcessInfo) -> bool:
    """Kernel threads have no executable and no argv; they are not userland
    programs and should not compete with unreviewed applications."""
    return (
        not process.exe
        and not process.cmdline
        and process.ppid in CONFIG.kernel_thread_parent_pids
    )


def is_zombie(process: ProcessInfo) -> bool:
    return process.state == "Z"


def weird_reason(process: ProcessInfo) -> str | None:
    """A pattern that deserves a human look, even if the name looks known."""
    if is_zombie(process):
        return "zombie: exited but not reaped by its parent"
    executable = process.exe or (process.cmdline[0] if process.cmdline else "")
    if process.exe.endswith(" (deleted)"):
        return "executable was deleted"
    if executable.startswith(SUSPICIOUS_DIRECTORIES):
        return f"executable runs from {executable.split('/', 3)[1]}/"
    known_name = process.name in SYSTEM_EXECUTABLES or process.name.startswith(
        SYSTEM_NAME_PREFIXES
    )
    if not known_name:
        return None
    executable_name = Path(executable).name
    if executable_name and not _name_matches(process.name, executable_name):
        return (
            f"system-looking name {process.name!r} but executable is "
            f"{executable_name!r}"
        )
    if executable.startswith("/") and not executable.startswith(SYSTEM_DIRECTORIES):
        return f"system-looking name {process.name!r} outside system directories"
    return None


def _name_matches(name: str, executable_name: str) -> bool:
    if name == executable_name:
        return True
    if executable_name in NAME_ALIASES.get(name, frozenset()):
        return True
    shorter, longer = sorted((name, executable_name), key=len)
    return longer.startswith(shorter)


def looks_like_system_process(process: ProcessInfo) -> bool:
    """A hint, never an automatic annotation: installed system software.

    The path is the useful signal; the name list catches kernel threads and
    helpers whose executable cannot be read.
    """
    if process.exe.startswith(SYSTEM_DIRECTORIES):
        return True
    return process.name.startswith(SYSTEM_NAME_PREFIXES)
