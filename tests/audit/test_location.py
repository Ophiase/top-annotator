from __future__ import annotations

from pathlib import Path

from top_annotator.__main__ import build_parser
from top_annotator.audit import BASE_AUDIT, AuditStore, default_audit_path
from top_annotator.audit.routing import active_scopes


def test_bundled_base_by_default() -> None:
    assert default_audit_path({}) == BASE_AUDIT


def test_variable_replaces_the_base() -> None:
    environment = {"TOP_ANNOTATOR_AUDIT": "~/shared/audit"}
    assert default_audit_path(environment) == Path.home() / "shared" / "audit"


def test_bundled_base_is_split_by_distribution() -> None:
    assert {path.name for path in BASE_AUDIT.iterdir()} >= {"common", "pop", "ubuntu"}


def test_a_machine_reads_only_its_own_distributions(tmp_path: Path) -> None:
    for scope in ("common", "pop", "arch"):
        (tmp_path / scope).mkdir()
        (tmp_path / scope / "entries.yaml").write_text(
            f"version: 1\nannotations:\n  '{scope}|/usr/bin/{scope}': safe\n",
            encoding="utf-8",
        )

    store = AuditStore.load(tmp_path, scopes=("common", "pop", "ubuntu"))

    assert sorted(store.annotations) == ["common|/usr/bin/common", "pop|/usr/bin/pop"]


def test_os_release_names_the_scopes(tmp_path: Path) -> None:
    release = tmp_path / "os-release"
    release.write_text('ID=pop\nID_LIKE="ubuntu debian"\n', encoding="utf-8")

    assert active_scopes(release) == ("common", "pop", "ubuntu", "debian")


def test_bundled_base_loads_annotations() -> None:
    assert AuditStore.load(BASE_AUDIT).annotations


def test_cache_flag_is_unset_by_default() -> None:
    assert build_parser().parse_args([]).cache is None
