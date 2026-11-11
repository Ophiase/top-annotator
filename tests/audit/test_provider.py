from __future__ import annotations

from pathlib import Path

from top_annotator.agent import annotate_session, snapshot_payload
from top_annotator.audit import BASE_AUDIT, AuditStore
from top_annotator.audit.routing import distribution_names
from top_annotator.core import PROVIDERS, provider_of
from top_annotator.core.category import Category

from ..factories import process


def test_provider_round_trips_and_survives_a_category_change(tmp_path: Path) -> None:
    path = tmp_path / "audit.yaml"
    AuditStore.load(path).set("tool|/usr/bin/tool", Category.SAFE, provider="distro")
    store = AuditStore.load(path)
    store.set("tool|/usr/bin/tool", Category.CORE)

    annotation = AuditStore.load(path).annotation_for("tool|/usr/bin/tool")

    assert annotation is not None
    assert annotation.provider == "distro"


def test_an_entry_without_provider_still_loads(tmp_path: Path) -> None:
    path = tmp_path / "audit.yaml"
    path.write_text(
        "version: 1\nannotations:\n  'tool|/usr/bin/tool': safe\n",
        encoding="utf-8",
    )

    annotation = AuditStore.load(path).annotation_for("tool|/usr/bin/tool")

    assert annotation is not None
    assert annotation.provider == ""


def test_a_kernel_thread_needs_no_entry_to_be_kernel() -> None:
    thread = process(42, 2, name="kworker/0:1", exe="")

    assert provider_of(thread, None) == "kernel"
    assert provider_of(process(7, 1), None) == ""


def test_snapshot_reports_the_provider(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit", session_path=tmp_path / "s.yaml")
    annotate_session(store, "pop|/usr/bin/pop", "safe", provider="pop")
    payload = snapshot_payload(
        store,
        (process(7, 1, name="pop", exe="/usr/bin/pop", signature="pop|/usr/bin/pop"),),
    )

    assert payload[0]["provider"] == "pop"


def test_every_base_entry_names_a_known_provider() -> None:
    store = AuditStore.load(BASE_AUDIT)

    unknown = {
        signature: annotation.provider
        for signature, annotation in store.annotations.items()
        if annotation.provider not in PROVIDERS
    }

    assert unknown == {}


def test_a_legacy_pop_provider_loads_as_derivative(tmp_path: Path) -> None:
    path = tmp_path / "audit.yaml"
    path.write_text(
        "version: 1\nannotations:\n  'tool|/usr/bin/tool':\n"
        "    category: safe\n    provider: pop\n",
        encoding="utf-8",
    )

    annotation = AuditStore.load(path).annotation_for("tool|/usr/bin/tool")

    assert annotation is not None
    assert annotation.provider == "derivative"


def test_os_release_names_the_base_and_the_derivative(tmp_path: Path) -> None:
    pop = tmp_path / "pop"
    pop.write_text(
        'NAME="Pop!_OS"\nID=pop\nID_LIKE="ubuntu debian"\n', encoding="utf-8"
    )
    arch = tmp_path / "arch"
    arch.write_text("NAME=Arch Linux\nID=arch\n", encoding="utf-8")

    assert distribution_names(pop) == {"distro": "ubuntu", "derivative": "pop"}
    assert distribution_names(arch) == {"distro": "arch"}
    assert distribution_names(tmp_path / "missing") == {}
