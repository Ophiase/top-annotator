from __future__ import annotations

from pathlib import Path

from top_annotator.audit import AuditStore
from top_annotator.core.category import Category


def test_round_trip_keeps_category_and_note(tmp_path: Path) -> None:
    path = tmp_path / "audit.yaml"
    store = AuditStore.load(path)
    store.set("tool|/usr/bin/tool", Category.SAFE, note="shipped by the distro")

    reloaded = AuditStore.load(path)
    annotation = reloaded.annotation_for("tool|/usr/bin/tool")

    assert annotation is not None
    assert annotation.category is Category.SAFE
    assert annotation.note == "shipped by the distro"


def test_hand_written_short_form_is_accepted(tmp_path: Path) -> None:
    path = tmp_path / "audit.yaml"
    path.write_text(
        "version: 1\nannotations:\n  'tool|/usr/bin/tool': safe\n",
        encoding="utf-8",
    )

    annotation = AuditStore.load(path).annotation_for("tool|/usr/bin/tool")

    assert annotation is not None
    assert annotation.category is Category.SAFE


def test_missing_file_starts_empty(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "missing.yaml")

    assert store.annotations == {}


def test_clear_removes_and_saves(tmp_path: Path) -> None:
    path = tmp_path / "audit.yaml"
    store = AuditStore.load(path)
    store.set("tool|/usr/bin/tool", Category.WATCH)
    store.clear("tool|/usr/bin/tool")

    assert AuditStore.load(path).annotations == {}


def test_directory_writes_one_file_per_family(tmp_path: Path) -> None:
    root = tmp_path / "audit"
    store = AuditStore.load(root)
    store.set("systemd|/sbin/init", Category.SAFE, family="system")
    store.set("gsd-color|/usr/libexec/gsd-color", Category.SAFE, family="gnome")

    assert (root / "system" / "misc.yaml").exists()
    assert (root / "gnome" / "misc.yaml").exists()
    assert len(AuditStore.load(root).annotations) == 2


def test_session_overlay_leaves_the_audit_file_untouched(tmp_path: Path) -> None:
    audit = tmp_path / "audit.yaml"
    audit.write_text(
        "version: 1\nannotations:\n  existing|/usr/bin/existing: safe\n",
        encoding="utf-8",
    )
    before = audit.read_text(encoding="utf-8")
    session = tmp_path / "cache" / "session.yaml"
    store = AuditStore.load(audit, session_path=session)
    store.set("tool|/usr/bin/tool", Category.TRUST)

    assert audit.read_text(encoding="utf-8") == before
    assert session.exists()
    assert AuditStore.load(audit, session_path=session).annotation_for(
        "tool|/usr/bin/tool"
    ) == store.annotation_for("tool|/usr/bin/tool")


def test_clearing_session_overlay_restores_the_audit_annotation(
    tmp_path: Path,
) -> None:
    audit = tmp_path / "audit.yaml"
    audit.write_text(
        "version: 1\nannotations:\n  existing|/usr/bin/existing: safe\n",
        encoding="utf-8",
    )
    session = tmp_path / "cache" / "session.yaml"
    store = AuditStore.load(audit, session_path=session)
    store.set("existing|/usr/bin/existing", Category.CORE)
    overridden = store.annotation_for("existing|/usr/bin/existing")
    assert overridden is not None
    assert overridden.category is Category.CORE

    store.clear("existing|/usr/bin/existing")

    annotation = store.annotation_for("existing|/usr/bin/existing")
    assert annotation is not None
    assert annotation.category is Category.SAFE


def test_nested_audit_files_are_loaded(tmp_path: Path) -> None:
    nested = tmp_path / "audit" / "system" / "boot.yaml"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        "version: 1\nannotations:\n  systemd|/sbin/init: core\n",
        encoding="utf-8",
    )

    store = AuditStore.load(tmp_path / "audit")

    annotation = store.annotation_for("systemd|/sbin/init")
    assert annotation is not None
    assert annotation.category is Category.CORE


def test_existing_annotation_keeps_its_family(tmp_path: Path) -> None:
    root = tmp_path / "audit"
    store = AuditStore.load(root)
    store.set("tool|/usr/bin/tool", Category.SAFE, family="system")
    store.set("tool|/usr/bin/tool", Category.WATCH, family="gnome")

    assert (root / "system" / "misc.yaml").exists()
    assert not (root / "gnome" / "misc.yaml").exists()


def test_children_round_trip_and_survive_a_category_change(tmp_path: Path) -> None:
    root = tmp_path / "audit"
    store = AuditStore.load(root)
    store.set("nginx|/usr/sbin/nginx", Category.SAFE, children=("nginx",))
    store.set("nginx|/usr/sbin/nginx", Category.WATCH)
    reloaded = AuditStore.load(root).annotations["nginx|/usr/sbin/nginx"]
    assert reloaded.category is Category.WATCH
    assert reloaded.children == ("nginx",)


def test_no_declaration_is_not_written(tmp_path: Path) -> None:
    root = tmp_path / "audit"
    AuditStore.load(root).set("tool|/usr/bin/tool", Category.SAFE, family="system")
    assert "children" not in (root / "system" / "misc.yaml").read_text(encoding="utf-8")


def test_exclusive_and_gui_round_trip(tmp_path: Path) -> None:
    root = tmp_path / "audit"
    AuditStore.load(root).set(
        "kitty|/usr/bin/kitty",
        Category.TRUST,
        children=("zsh",),
        flags={"exclusive": True, "gui": True},
    )
    reloaded = AuditStore.load(root).annotations["kitty|/usr/bin/kitty"]
    assert (reloaded.children, reloaded.exclusive, reloaded.gui) == (
        ("zsh",),
        True,
        True,
    )
