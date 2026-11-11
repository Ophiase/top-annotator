from __future__ import annotations

from dataclasses import dataclass

from ...core.category import Category


@dataclass(frozen=True, slots=True)
class RuleRow:
    signature: str
    category: Category
    note: str
    source: str
    changed: str = ""
