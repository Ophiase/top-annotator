from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from ..process.heuristics import is_kernel_thread

if TYPE_CHECKING:
    from .annotation import Annotation
    from .process_info import ProcessInfo


class Category(StrEnum):
    PERSONAL = "personal"
    TRUST = "trust"
    HOST = "host"
    AUDITED = "audited"
    SAFE = "safe"
    CORE = "core"
    WATCH = "watch"
    UNSAFE = "unsafe"


CATEGORY_ORDER: tuple[Category, ...] = (
    Category.TRUST,
    Category.HOST,
    Category.AUDITED,
    Category.SAFE,
    Category.CORE,
    Category.PERSONAL,
    Category.WATCH,
    Category.UNSAFE,
)

TRUST_CHOICES: tuple[Category, ...] = (
    Category.CORE,
    Category.SAFE,
    Category.AUDITED,
    Category.HOST,
    Category.TRUST,
    Category.PERSONAL,
    Category.WATCH,
    Category.UNSAFE,
)


def next_category(current: Category | None) -> Category | None:
    if current is None:
        return CATEGORY_ORDER[0]
    index = CATEGORY_ORDER.index(current)
    if index + 1 == len(CATEGORY_ORDER):
        return None
    return CATEGORY_ORDER[index + 1]


PROVIDERS: dict[str, str] = {
    "app": "a program you drive (a window, a terminal, an editor) and its helpers",
    "service": "a third-party program that stays up in the background: a daemon, a VPN",
    "desktop": "the desktop session's own plumbing: GNOME or COSMIC shell, settings",
    "derivative": "a package the derivative distribution makes or patches on its base",
    "distro": "a package of the base distribution, shipped unchanged",
    "systemd": "systemd: PID 1 and its own daemons",
    "kernel": "the Linux kernel: its threads and modules",
}
LEGACY_PROVIDERS: dict[str, str] = {"pop": "derivative"}


def provider_of(process: ProcessInfo, annotation: Annotation | None) -> str:
    """Who ships the process: the annotation says it, a kernel thread needs no entry."""
    if annotation is not None and annotation.provider:
        return annotation.provider
    return "kernel" if is_kernel_thread(process) else ""
