from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from ..annotation import SHELLS, Annotation
from ..process_info import ProcessInfo

if TYPE_CHECKING:
    from .process_tree import ProcessTree


def vouched(
    tree: ProcessTree,
    process: ProcessInfo,
    annotations: Mapping[str, Annotation],
) -> bool:
    """Something allowed accounts for it: a covering parent, an agent, a
    shell that is itself accounted for, or a command run from such a shell."""
    parent = tree.parent_of(process)
    if parent is None:
        return False
    covering = tree.parent_annotation(process, annotations)
    if covering is not None and covering.covers(process.name):
        return True
    if tree.agent_shell(process, annotations):
        return True
    if parent.name in SHELLS:
        return accounted_shell(tree, parent, annotations)
    launcher = tree.parent_of(parent)
    return (
        launcher is not None
        and launcher.name in SHELLS
        and accounted_shell(tree, launcher, annotations)
    )


def accounted_shell(
    tree: ProcessTree,
    shell: ProcessInfo,
    annotations: Mapping[str, Annotation],
) -> bool:
    return shell.signature in annotations or vouched(tree, shell, annotations)
