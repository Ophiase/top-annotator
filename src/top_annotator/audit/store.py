from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path

from ..core.annotation import Annotation
from ..core.category import Category
from .journal import HISTORY_FILENAME, Journal, restored
from .review import RuleRow, Suggestions
from .routing import active_scopes
from .yaml_io import (
    CACHE_SUFFIXES,
    cache_files,
    read_annotations,
    write_annotations,
)

__all__ = ["AuditStore"]


@dataclass
class AuditStore:
    root: Path
    annotations: dict[str, Annotation] = field(default_factory=dict)
    origins: dict[str, Path] = field(default_factory=dict)
    files: dict[Path, dict[str, Annotation]] = field(default_factory=dict)
    session_path: Path | None = None
    session: dict[str, Annotation] = field(default_factory=dict)
    journal: Journal | None = None
    scopes: tuple[str, ...] = ()
    suggestions: Suggestions = field(default_factory=Suggestions)

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        session_path: Path | None = None,
        scopes: tuple[str, ...] | None = None,
    ) -> AuditStore:
        store = cls(root=path, session_path=session_path)
        store.scopes = active_scopes() if scopes is None else scopes
        store.suggestions = Suggestions.load(path, store.scopes)
        for file in cache_files(path, store.scopes):
            loaded = read_annotations(file)
            store.files[file] = loaded
            for signature, annotation in loaded.items():
                store.annotations[signature] = annotation
                store.origins[signature] = file
        if session_path is not None:
            store.session = read_annotations(session_path)
            store.annotations.update(store.session)
            store.journal = Journal(session_path.with_name(HISTORY_FILENAME))
        return store

    def annotation_for(self, signature: str) -> Annotation | None:
        return self.annotations.get(signature)

    def accept_suggestion(self, signature: str) -> Annotation | None:
        """Copy the base's suggestion into the user's layer, as their decision."""
        suggestion = self.suggestions.get(signature)
        if suggestion is None or signature in self.annotations:
            return None
        return self.set(
            signature,
            suggestion.category,
            suggestion.note,
            provider=suggestion.provider,
            children=suggestion.children,
            flags=suggestion.flags(),
            agents=suggestion.agents,
            plugin_args=suggestion.plugin_args,
        )

    def source_for(self, signature: str) -> str:
        if signature in self.session:
            return "session"
        origin = self.origins.get(signature)
        if origin is None:
            return ""
        if origin == self.root:
            return origin.name
        try:
            return str(origin.relative_to(self.root))
        except ValueError:
            return origin.name

    def rule_rows(self) -> tuple[RuleRow, ...]:
        """Every effective rule, the most recently changed first."""
        history = self.journal.history() if self.journal else {}
        rows = [
            RuleRow(
                signature,
                annotation.category,
                annotation.note,
                self.source_for(signature),
                history[signature][1]
                if signature in history and signature in self.session
                else annotation.updated.isoformat(),
            )
            for signature, annotation in self.annotations.items()
        ]
        rows.sort(key=lambda row: (row.changed, row.signature), reverse=True)
        return tuple(rows)

    def set(
        self,
        signature: str,
        category: Category,
        note: str | None = None,
        *,
        provider: str | None = None,
        family: str = "programs",
        children: tuple[str, ...] | None = None,
        flags: Mapping[str, bool] | None = None,
        agents: tuple[str, ...] | None = None,
        plugin_args: tuple[str, ...] | None = None,
    ) -> Annotation:
        existing = self.annotations.get(signature) or Annotation(category=category)
        annotation = replace(
            existing,
            category=category,
            note=existing.note if note is None else note,
            provider=existing.provider if provider is None else provider,
            updated=date.today(),
            children=existing.children if children is None else children,
            agents=existing.agents if agents is None else agents,
            plugin_args=existing.plugin_args if plugin_args is None else plugin_args,
            **(flags or {}),
        )
        if self.session_path is not None:
            self._change_session(signature, annotation)
            return annotation
        target = self.origins.get(signature) or self._file_for(family)
        self.files.setdefault(target, {})[signature] = annotation
        self.annotations[signature] = annotation
        self.origins[signature] = target
        self.save_file(target)
        return annotation

    def clear(self, signature: str) -> bool:
        if self.session_path is not None:
            if signature not in self.session:
                return False
            self._change_session(signature, None)
            return True
        annotation = self.annotations.pop(signature, None)
        if annotation is None:
            return False
        target = self.origins.pop(signature, None)
        if target is not None:
            self.files.get(target, {}).pop(signature, None)
            self.save_file(target)
        return True

    def undo(self) -> str | None:
        """Put back the session entry the latest change replaced; the
        signature it touched, or None when there is nothing to undo."""
        change = self.journal.undoable() if self.journal else None
        if change is None or self.journal is None:
            return None
        signature = change["signature"]
        self.journal.record(
            signature,
            self.session.get(signature),
            self._put_session(signature, restored(change)),
            reverts=change["id"],
        )
        return signature

    def _change_session(self, signature: str, annotation: Annotation | None) -> None:
        before = self.session.get(signature)
        self._put_session(signature, annotation)
        if self.journal is not None:
            self.journal.record(signature, before, annotation)

    def _put_session(
        self, signature: str, annotation: Annotation | None
    ) -> Annotation | None:
        if annotation is not None:
            self.session[signature] = annotation
            self.annotations[signature] = annotation
        else:
            self.session.pop(signature, None)
            audit_annotation, audit_file = self._audit_annotation(signature)
            if audit_annotation is not None and audit_file is not None:
                self.annotations[signature] = audit_annotation
                self.origins[signature] = audit_file
            else:
                self.annotations.pop(signature, None)
                self.origins.pop(signature, None)
        self._save_session()
        return annotation

    def save(self) -> None:
        for path in self.files:
            self.save_file(path)
        if self.session_path is not None:
            self._save_session()

    def save_file(self, path: Path) -> None:
        write_annotations(path, self.files.get(path, {}))

    def _save_session(self) -> None:
        if self.session_path is not None:
            write_annotations(
                self.session_path,
                self.session,
                shareable=False,
            )

    def _audit_annotation(
        self,
        signature: str,
    ) -> tuple[Annotation | None, Path | None]:
        for path, entries in self.files.items():
            annotation = entries.get(signature)
            if annotation is not None:
                return annotation, path
        return None, None

    def _file_for(self, family: str) -> Path:
        if self.root.suffix in CACHE_SUFFIXES:
            return self.root
        return self.root / family / "misc.yaml"
