from pathlib import Path

from top_annotator.audit import AuditStore
from top_annotator.core.category import Category

SUGGESTION = """version: 1
annotations:
  dockerd|/usr/bin/dockerd:
    category: safe
    provider: service
    note: Docker daemon
"""


def _base(tmp_path: Path) -> Path:
    base = tmp_path / "base"
    folder = base / "common" / "programs" / "suggestions"
    folder.mkdir(parents=True)
    (folder / "docker.yaml").write_text(SUGGESTION, encoding="utf-8")
    return base


def test_a_suggestion_is_offered_never_trusted(tmp_path: Path) -> None:
    store = AuditStore.load(_base(tmp_path), scopes=("common",))

    assert store.annotation_for("dockerd|/usr/bin/dockerd") is None
    assert store.suggestions.get("dockerd|/usr/bin/dockerd") is not None


def test_accepting_writes_the_users_layer(tmp_path: Path) -> None:
    session = tmp_path / "data" / "session.yaml"
    store = AuditStore.load(_base(tmp_path), session_path=session, scopes=("common",))

    accepted = store.accept_suggestion("dockerd|/usr/bin/dockerd")

    assert accepted is not None
    assert accepted.category is Category.SAFE
    assert accepted.provider == "service"
    assert store.source_for("dockerd|/usr/bin/dockerd") == "session"
    assert store.undo() == "dockerd|/usr/bin/dockerd"
    assert store.annotation_for("dockerd|/usr/bin/dockerd") is None


def test_an_annotated_process_takes_no_suggestion(tmp_path: Path) -> None:
    session = tmp_path / "data" / "session.yaml"
    store = AuditStore.load(_base(tmp_path), session_path=session, scopes=("common",))
    store.set("dockerd|/usr/bin/dockerd", Category.WATCH)

    assert store.accept_suggestion("dockerd|/usr/bin/dockerd") is None
