from __future__ import annotations

from pathlib import Path

from top_annotator.audit import AuditStore
from top_annotator.core.category import Category

TOOL = "tool|/usr/bin/tool"


def session_store(tmp_path: Path) -> AuditStore:
    audit = tmp_path / "audit.yaml"
    audit.write_text(
        f"version: 1\nannotations:\n  '{TOOL}': safe\n",
        encoding="utf-8",
    )
    return AuditStore.load(audit, session_path=tmp_path / "data" / "session.yaml")


def test_every_session_change_is_journaled(tmp_path: Path) -> None:
    store = session_store(tmp_path)
    store.set(TOOL, Category.TRUST)
    store.set(TOOL, Category.WATCH)
    store.clear(TOOL)

    assert store.journal is not None
    first, last, count = store.journal.history()[TOOL]
    assert count == 3
    assert first <= last


def test_undo_walks_back_one_change_at_a_time(tmp_path: Path) -> None:
    store = session_store(tmp_path)
    store.set(TOOL, Category.TRUST, note="mine")
    store.set(TOOL, Category.WATCH)

    assert store.undo() == TOOL
    annotation = store.annotation_for(TOOL)
    assert annotation is not None
    assert annotation.category is Category.TRUST
    assert annotation.note == "mine"

    assert store.undo() == TOOL
    annotation = store.annotation_for(TOOL)
    assert annotation is not None
    assert annotation.category is Category.SAFE
    assert TOOL not in store.session

    assert store.undo() is None


def test_undo_survives_a_restart(tmp_path: Path) -> None:
    session_store(tmp_path).set(TOOL, Category.UNSAFE)

    store = session_store(tmp_path)
    store.undo()

    reloaded = session_store(tmp_path).annotation_for(TOOL)
    assert reloaded is not None
    assert reloaded.category is Category.SAFE


def test_review_rows_put_the_latest_change_first(tmp_path: Path) -> None:
    store = session_store(tmp_path)
    store.set("other|/usr/bin/other", Category.TRUST)

    rows = store.rule_rows()

    assert rows[0].signature == "other|/usr/bin/other"
    assert "T" in rows[0].changed
