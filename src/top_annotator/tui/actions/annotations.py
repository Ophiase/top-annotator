from __future__ import annotations

from functools import partial
from typing import Any

from ...audit import family_for
from ...core import Annotation, Category, ProcessInfo, SectionHeader, next_category
from ...process.verify import inspect_executable
from ..presentation import TRUST_LABELS, UNREVIEWED, group_meaning
from ..screens import (
    ChoiceScreen,
    DetailScreen,
    GroupScreen,
    NoteScreen,
    ReviewScreen,
)
from ..table import ProcessTable


class AnnotationActions:
    def action_show_detail(self: Any) -> None:
        index = self.query_one(ProcessTable).cursor_row
        if 0 <= index < len(self._rows) and isinstance(
            self._rows[index], SectionHeader
        ):
            self._show_group(self._rows[index])
            return
        process = self._selected_process()
        if process is None or self._tree is None:
            return
        source = process.exe or (process.cmdline[0] if process.cmdline else "")
        self.push_screen(
            DetailScreen(
                process,
                self._store.annotation_for(process.signature),
                self._tree.parent_chain(process),
                self._tree.parent_annotation(process, self._store.annotations),
                self._tree.typed(process, self._store.annotations),
                inspect_executable(source, self._verification_cache),
                self._history_line(process.signature),
                self._store.suggestions.get(process.signature),
            ),
            self._focus_table,
        )

    def _show_group(self: Any, header: SectionHeader) -> None:
        if self._tree is None:
            return
        members = tuple(
            process for process in self._tree.processes if process.pid in header.pids
        )
        self.push_screen(
            GroupScreen(
                header, group_meaning(header), members, self._store.annotations
            ),
            self._focus_table,
        )

    def _history_line(self: Any, signature: str) -> str:
        journal = self._store.journal
        history = journal.history().get(signature) if journal else None
        if history is None:
            return ""
        first, last, count = history
        return f"first {first} · last {last} · {count} change(s)"

    def _focus_table(self: Any, _result: None) -> None:
        self.query_one(ProcessTable).focus()

    def action_mark_trust(self: Any) -> None:
        self._annotate(Category.TRUST)

    def action_show_review(self: Any) -> None:
        self.push_screen(ReviewScreen(self._store.rule_rows()), self._focus_table)

    def action_choose_trust(self: Any) -> None:
        targets = self._targets()
        if not targets:
            return
        annotation = self._store.annotation_for(targets[0].signature)
        title = (
            targets[0].signature if len(targets) == 1 else f"{len(targets)} processes"
        )
        self.push_screen(
            ChoiceScreen(
                title,
                TRUST_LABELS,
                annotation.category.value if annotation else None,
            ),
            partial(self._save_trust, targets),
        )

    def _save_trust(
        self: Any, targets: tuple[ProcessInfo, ...], choice: str | None
    ) -> None:
        self.query_one(ProcessTable).focus()
        if choice is not None:
            self._apply(targets, None if choice == UNREVIEWED else Category(choice))

    def action_cycle_category(self: Any) -> None:
        process = self._selected_process()
        if process is None:
            return
        current = self._store.annotation_for(process.signature)
        self._annotate(next_category(current.category if current else None))

    def _annotate(self: Any, category: Category | None) -> None:
        self._apply(self._targets(), category)

    def _apply(
        self: Any, targets: tuple[ProcessInfo, ...], category: Category | None
    ) -> None:
        for process in targets:
            if category is None:
                self._store.clear(process.signature)
            else:
                self._store.set(process.signature, category, family=family_for(process))
        self._leave_visual()
        self._render()
        label = category.value if category else "unannotated"
        if len(targets) == 1:
            self.notify(f"{targets[0].name}[{targets[0].pid}] → {label}", timeout=1.5)
        elif targets:
            self.notify(f"{len(targets)} processes → {label}", timeout=2)

    def action_accept_suggestion(self: Any) -> None:
        on_header = self._visual_anchor is None and self._header_members()
        targets = self._header_members() if on_header else self._targets()
        accepted = [
            process
            for process in targets
            if self._store.accept_suggestion(process.signature) is not None
        ]
        self._leave_visual()
        if not accepted:
            self.notify("no suggestion to accept here", timeout=1.5)
            return
        self._render()
        self.notify(f"{len(accepted)} suggestion(s) accepted; u undoes one", timeout=2)

    def action_clear_annotation(self: Any) -> None:
        self._annotate(None)

    def action_undo(self: Any) -> None:
        signature = self._store.undo()
        if signature is None:
            self.notify("nothing to undo", timeout=1.5)
            return
        self._render()
        annotation = self._store.annotation_for(signature)
        label = annotation.category.value if annotation else "unannotated"
        self.notify(f"undo: {signature} → {label}", timeout=2.5)

    def action_edit_note(self: Any) -> None:
        process = self._selected_process()
        if process is None:
            return
        annotation = self._store.annotation_for(process.signature)
        self.push_screen(
            NoteScreen(process.signature, annotation.note if annotation else ""),
            partial(self._save_note, process, annotation),
        )

    def _save_note(
        self: Any,
        process: ProcessInfo,
        annotation: Annotation | None,
        note: str | None,
    ) -> None:
        if note is None:
            return
        category = annotation.category if annotation else Category.AUDITED
        self._store.set(
            process.signature,
            category,
            note=note,
            family=family_for(process),
        )
        self._render()
        self.query_one(ProcessTable).focus()
