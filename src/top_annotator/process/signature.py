from __future__ import annotations

from pathlib import Path

INTERPRETER_NAMES = frozenset({
    "bash",
    "bun",
    "deno",
    "fish",
    "node",
    "perl",
    "python",
    "python3",
    "ruby",
    "sh",
    "zsh",
})


def process_signature(
    name: str,
    exe: str,
    cmdline: tuple[str, ...],
) -> str:
    """A stable key for one kind of process: name, executable and script.

    The script is part of the key because every Python or Node program shares
    the same interpreter executable; without it, annotating one script would
    silently annotate all of them.
    """
    executable = _clean_path(exe) or _command_executable(cmdline) or name
    script = _script_argument(name, executable, cmdline)
    parts = [name, executable, script] if script else [name, executable]
    return "|".join(parts)


def _clean_path(path: str) -> str:
    return path.removesuffix(" (deleted)")


def _command_executable(cmdline: tuple[str, ...]) -> str:
    """Root processes often hide /proc/<pid>/exe from an unprivileged reader;
    their own argv[0] is the next best identity."""
    if not cmdline:
        return ""
    candidate = _clean_path(cmdline[0])
    return candidate if candidate.startswith("/") else ""


def _script_argument(name: str, executable: str, cmdline: tuple[str, ...]) -> str:
    interpreter = Path(executable).name
    if name not in INTERPRETER_NAMES and interpreter not in INTERPRETER_NAMES:
        return ""
    arguments = cmdline[1:]
    for index, argument in enumerate(arguments):
        if argument == "-c":
            return _inline_command(arguments[index + 1 : index + 2])
        if argument.startswith("-"):
            continue
        if argument == executable or Path(argument).name == name:
            continue
        return _absolute_script(argument)
    return ""


def _inline_command(command: tuple[str, ...]) -> str:
    """Inline code changes every run; only its first word stays stable."""
    words = command[0].split() if command else []
    return f"-c {words[0]}" if words else "-c"


def _absolute_script(argument: str) -> str:
    path = Path(argument)
    return str(path.resolve()) if path.is_absolute() else argument
