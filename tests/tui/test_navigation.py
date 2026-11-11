from __future__ import annotations

import asyncio
from pathlib import Path

from textual.widgets import DataTable

from top_annotator.audit import AuditStore
from top_annotator.core.category import Category
from top_annotator.core.section_header import SectionHeader
from top_annotator.core.tree import ProcessRow
from top_annotator.tui import TopAnnotatorApp

from .fake_scanner import SYSTEMD, FakeScanner


def test_a_group_unfolds_alone_and_folds_stay_in_their_band(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    store.set(SYSTEMD, Category.CORE, provider="systemd")
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)
    seen: dict[str, list[str]] = {}

    async def scenario() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            seen["start"] = [row.key for row in app._rows]
            group = next(
                index
                for index, row in enumerate(app._rows)
                if isinstance(row, SectionHeader) and row.group == "systemd"
            )
            app.query_one(DataTable).move_cursor(row=group)
            await pilot.press("space")
            await pilot.pause()
            app.query_one(DataTable).move_cursor(row=1)
            await pilot.press("space")
            await pilot.pause()
            seen["folded"] = [
                row.key
                for row in app._rows
                if isinstance(row, ProcessRow) and row.folded
            ]
            seen["end"] = [row.key for row in app._rows]

    asyncio.run(scenario())
    assert seen["start"] == ["NEW", "NEW#1", "NEW#2", "SAFE", "SAFE/systemd"]
    assert seen["folded"] == ["NEW#1"]
    assert "SAFE/systemd#1" in seen["end"]


def test_the_trust_menu_can_return_a_process_to_unreviewed(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    store.set(SYSTEMD, Category.SAFE)
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            row = next(
                index
                for index, row in enumerate(app._rows)
                if isinstance(row, ProcessRow) and row.process.pid == 1
            )
            app.query_one(DataTable).move_cursor(row=row)
            await pilot.press("S")
            await pilot.pause()
            await pilot.press("end", "enter")
            await pilot.pause()

    asyncio.run(scenario())
    assert store.annotation_for(SYSTEMD) is None


def test_the_filter_menu_replaces_the_unreviewed_toggle(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    store.set(SYSTEMD, Category.CORE, provider="systemd")
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)
    shown: list[int] = []

    async def scenario() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("f")
            await pilot.pause()
            assert type(app.screen).__name__ == "ChoiceScreen"
            await pilot.press("down", "enter")
            await pilot.pause()
            shown.extend(
                row.process.pid for row in app._rows if isinstance(row, ProcessRow)
            )

    asyncio.run(scenario())
    assert app._filter == "unreviewed"
    assert shown == [1, 2]


def test_u_undoes_an_accidental_key(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml", session_path=tmp_path / "s.yaml")
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("s")
            await pilot.pause()
            await pilot.press("u")
            await pilot.pause()

    asyncio.run(scenario())
    assert store.annotation_for(SYSTEMD) is None


def test_y_copies_the_selected_process(tmp_path: Path, monkeypatch) -> None:
    copied: list[str] = []
    monkeypatch.setattr(
        "top_annotator.tui.actions.view.copy_with_wl",
        lambda text: copied.append(text) or True,
    )
    store = AuditStore.load(tmp_path / "audit.yaml")
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("y")
            await pilot.pause()

    asyncio.run(scenario())
    assert copied
    assert copied[0].startswith("signature  ")
    assert "parents    systemd[1]" in copied[0]


def test_enter_on_a_group_header_explains_the_group(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    store.set(SYSTEMD, Category.CORE, provider="systemd")
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)
    opened: list[str] = []

    async def scenario() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            group = next(
                index
                for index, row in enumerate(app._rows)
                if isinstance(row, SectionHeader) and row.group == "systemd"
            )
            app.query_one(DataTable).move_cursor(row=group)
            await pilot.press("enter")
            await pilot.pause()
            opened.append(type(app.screen).__name__)

    asyncio.run(scenario())
    assert opened == ["GroupScreen"]
