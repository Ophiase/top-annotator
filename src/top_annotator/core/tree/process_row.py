from __future__ import annotations

from dataclasses import dataclass

from ..process_info import ProcessInfo
from ..section_header import SectionHeader

TREE_SCOPE = "tree"


@dataclass(frozen=True, slots=True)
class ProcessRow:
    process: ProcessInfo
    depth: int
    prefix: str
    has_children: bool
    folded: bool
    is_context: bool = False
    key: str = ""


Row = ProcessRow | SectionHeader


def fold_key(scope: str, pid: int) -> str:
    """A fold belongs to the place it was made: the same PID shown in two
    bands folds independently in each."""
    return f"{scope}#{pid}"
