from __future__ import annotations

from collections.abc import Mapping

from ...annotation import Annotation
from ...category import PROVIDERS, provider_of
from ...process_info import ProcessInfo

UNLABELLED = "unlabelled"
KERNEL = "kernel"
# Riskiest first: an entry nobody labelled, then what sits on top of the
# system, down to the kernel.
GROUP_ORDER: tuple[str, ...] = (
    UNLABELLED,
    *(provider for provider in PROVIDERS if provider != KERNEL),
    KERNEL,
)
OPEN_GROUPS = frozenset({UNLABELLED, "app", "service", "desktop"})


def provider_groups(
    members: list[ProcessInfo],
    annotations: Mapping[str, Annotation],
    by_pid: Mapping[int, ProcessInfo],
) -> list[tuple[str, list[ProcessInfo]]]:
    """The SAFE band split by provider, riskiest first: `other`, any
    hand-written provider, then the known ones down to the kernel."""
    groups: dict[str, list[ProcessInfo]] = {}
    for process in members:
        groups.setdefault(group_of(process, annotations, by_pid), []).append(process)
    hand_written = sorted(set(groups) - set(GROUP_ORDER))
    known = [group for group in GROUP_ORDER if group in groups]
    order = (
        known[:1] + hand_written + known[1:]
        if UNLABELLED in groups
        else hand_written + known
    )
    return [(group, groups[group]) for group in order]


def group_of(
    process: ProcessInfo,
    annotations: Mapping[str, Annotation],
    by_pid: Mapping[int, ProcessInfo],
) -> str:
    """A process with no entry of its own, a shell its terminal covers, sits
    with the nearest ancestor that names a provider."""
    seen: set[int] = set()
    current: ProcessInfo | None = process
    while current is not None and current.pid not in seen:
        seen.add(current.pid)
        annotation = annotations.get(current.signature)
        provider = provider_of(current, annotation)
        if provider:
            return provider
        if annotation is not None:
            return UNLABELLED
        current = by_pid.get(current.ppid)
    return UNLABELLED


def common_chain(
    members: list[ProcessInfo],
    by_pid: Mapping[int, ProcessInfo],
) -> tuple[ProcessInfo, ...]:
    """The ancestors every process of the group shares, outside the group,
    nearest first: the header writes them as `∈ a ∈ b`, the rows hang below."""
    inside = {process.pid for process in members}
    chains = [
        ancestors(process, by_pid) for process in members if process.ppid not in inside
    ]
    if not chains or not all(chains):
        return ()
    shared: list[ProcessInfo] = []
    for level in zip(*chains, strict=False):
        if any(process.pid != level[0].pid for process in level):
            break
        shared.append(level[0])
    return tuple(reversed(shared))


def ancestors(
    process: ProcessInfo,
    by_pid: Mapping[int, ProcessInfo],
) -> list[ProcessInfo]:
    """The ancestors of a process, the root first."""
    chain: list[ProcessInfo] = []
    seen = {process.pid}
    current = by_pid.get(process.ppid)
    while current is not None and current.pid not in seen:
        chain.append(current)
        seen.add(current.pid)
        current = by_pid.get(current.ppid)
    return list(reversed(chain))
