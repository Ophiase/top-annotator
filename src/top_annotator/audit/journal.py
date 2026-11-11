from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.annotation import Annotation
from .yaml_io import entry_of, parse_annotation

HISTORY_FILENAME = "history.jsonl"


class Journal:
    """Append-only log of every change to the user's layer.

    One JSON line per change: when, which signature, the entry before and
    after. An undo is itself a change that names the one it reverts, so the
    log never loses a state and tells when a rule was first and last set.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        entries: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict) and "signature" in entry:
                entries.append(entry)
        return entries

    def record(
        self,
        signature: str,
        before: Annotation | None,
        after: Annotation | None,
        *,
        reverts: int | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "id": len(self.entries()) + 1,
            "at": datetime.now().isoformat(timespec="seconds"),
            "signature": signature,
            "before": entry_of(before) if before else None,
            "after": entry_of(after) if after else None,
        }
        if reverts is not None:
            entry["reverts"] = reverts
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def undoable(self) -> dict[str, Any] | None:
        """The latest change that is not an undo and was not undone yet."""
        entries = self.entries()
        reverted = {entry["reverts"] for entry in entries if "reverts" in entry}
        for entry in reversed(entries):
            if "reverts" not in entry and entry.get("id") not in reverted:
                return entry
        return None

    def history(self) -> dict[str, tuple[str, str, int]]:
        """Per signature: first change, last change, number of changes."""
        seen: dict[str, tuple[str, str, int]] = {}
        for entry in self.entries():
            signature, at = entry["signature"], str(entry.get("at", ""))
            first, _, count = seen.get(signature, (at, at, 0))
            seen[signature] = (first, at, count + 1)
        return seen


def restored(change: dict[str, Any]) -> Annotation | None:
    """The annotation a change replaced, as an undo puts it back."""
    return parse_annotation(change["before"]) if change.get("before") else None
