from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .process_info import ProcessInfo
from .section import Section


@dataclass(frozen=True, slots=True)
class SectionHeader:
    """A band (`group` empty) or a provider group inside a band, with the
    totals of the processes it holds. A group shows its processes without the
    ancestors from other groups; `parents` names where its subtrees attach."""

    section: Section
    count: int
    group: str = ""
    folded: bool = False
    rss_bytes: int = 0
    cpu_percent: float = 0.0
    parents: tuple[str, ...] = ()
    pids: tuple[int, ...] = ()

    @classmethod
    def build(
        cls,
        section: Section,
        members: Sequence[ProcessInfo],
        folded: frozenset[str],
        group: str = "",
        parents: tuple[str, ...] = (),
    ) -> SectionHeader:
        return cls(
            section,
            len(members),
            group,
            key_of(section, group) in folded,
            sum(process.rss_bytes for process in members),
            sum(process.cpu_percent for process in members),
            parents,
            tuple(process.pid for process in members),
        )

    @property
    def key(self) -> str:
        return key_of(self.section, self.group)


def key_of(section: Section, group: str = "") -> str:
    return f"{section.value}/{group}" if group else section.value
