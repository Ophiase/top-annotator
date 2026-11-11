from __future__ import annotations

from enum import StrEnum

from ..process.heuristics import is_kernel_thread, is_zombie, weird_reason
from .annotation import SHELLS, Annotation
from .category import Category
from .process_info import ProcessInfo


class Section(StrEnum):
    WEIRD = "WEIRD"
    NEW = "NEW"
    SAFE = "SAFE"


SECTION_ORDER = (Section.WEIRD, Section.NEW, Section.SAFE)


def typed_in_terminal(
    parent: ProcessInfo | None,
    grandparent: Annotation | None,
) -> bool:
    """Its parent is a shell that a `terminal` entry covers: the user typed it."""
    return (
        parent is not None
        and parent.name in SHELLS
        and grandparent is not None
        and grandparent.terminal
    )


def stray_shell(
    process: ProcessInfo,
    annotation: Annotation | None,
    *,
    vouched: bool,
) -> bool:
    """A shell with no entry of its own that no allowed parent accounts for."""
    return process.name in SHELLS and annotation is None and not vouched


POSITIVE = frozenset({
    Category.TRUST,
    Category.HOST,
    Category.AUDITED,
    Category.SAFE,
    Category.CORE,
    Category.PERSONAL,
})


def known_zombie(process: ProcessInfo, annotation: Annotation | None) -> bool:
    """A dead process cannot act: once the human has identified it, its
    zombie state is noise, not a prompt."""
    return (
        is_zombie(process)
        and annotation is not None
        and annotation.category in POSITIVE
    )


def section_for(
    process: ProcessInfo,
    annotation: Annotation | None,
    parent: Annotation | None = None,
    *,
    typed: bool = True,
    agent_shell: bool = False,
    vouched: bool = True,
) -> Section:
    if is_kernel_thread(process):
        return Section.SAFE
    if weird_reason(process) is not None and not known_zombie(process, annotation):
        return Section.WEIRD
    if parent is not None and parent.forbids(process.name):
        return Section.WEIRD
    if stray_shell(process, annotation, vouched=vouched):
        return Section.WEIRD
    if annotation is not None and annotation.interactive and not typed:
        return Section.WEIRD
    if annotation is not None and annotation.category in {
        Category.WATCH,
        Category.UNSAFE,
    }:
        return Section.WEIRD
    if annotation is not None and annotation.category in POSITIVE:
        return Section.SAFE
    if annotation is None and parent is not None and parent.covers(process.name):
        return Section.SAFE
    if annotation is None and agent_shell:
        return Section.SAFE
    return Section.NEW


def section_reason(
    process: ProcessInfo,
    annotation: Annotation | None,
    parent: Annotation | None = None,
    *,
    typed: bool = True,
    vouched: bool = True,
) -> str:
    reason = weird_reason(process)
    if reason is not None and not known_zombie(process, annotation):
        return reason
    if parent is not None and parent.forbids(process.name):
        expected = ", ".join(parent.children or ()) or "none"
        return f"unexpected child of its parent (expected: {expected})"
    if stray_shell(process, annotation, vouched=vouched):
        return "a shell that no terminal, agent or allowed parent started"
    if annotation is not None and annotation.interactive and not typed:
        return "expected only from a user terminal, started elsewhere"
    if annotation is not None and annotation.category in {
        Category.WATCH,
        Category.UNSAFE,
    }:
        return f"annotated {annotation.category.value}"
    return ""
