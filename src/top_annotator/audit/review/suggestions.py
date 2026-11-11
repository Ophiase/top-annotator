from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from ...core.annotation import Annotation
from ..yaml_io import read_annotations, suggestion_files


@dataclass(frozen=True, slots=True)
class Suggestions:
    """Entries the base offers for optional programs. A suggestion never
    changes what is trusted: the human accepts it into their own layer."""

    entries: Mapping[str, Annotation] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path, scopes: tuple[str, ...]) -> Suggestions:
        entries: dict[str, Annotation] = {}
        for file in suggestion_files(root, scopes):
            entries.update(read_annotations(file))
        return cls(entries)

    def get(self, signature: str) -> Annotation | None:
        return self.entries.get(signature)
