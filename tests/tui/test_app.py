from __future__ import annotations

import asyncio
from pathlib import Path

from textual.widgets import DataTable

from top_annotator.audit import AuditStore
from top_annotator.core.category import Category
from top_annotator.core.section import Section
from top_annotator.core.section_header import SectionHeader
from top_annotator.tui import TopAnnotatorApp

from .fake_scanner import SYSTEMD, FakeScanner
from .many_scanner import ManyScanner


def test_app_renders_and_marks_trust(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one(DataTable)
            assert table.row_count == 3
            first = app._rows[0]
            assert isinstance(first, SectionHeader)
            assert first.section is Section.NEW
            await pilot.press("enter")
            await pilot.pause()
            assert len(app.screen_stack) == 2
            await pilot.press("escape")
            await pilot.pause()
            await pilot.press("s")
            await pilot.pause()

    asyncio.run(scenario())
    annotation = store.annotation_for(SYSTEMD)
    assert annotation is not None
    assert annotation.category is Category.TRUST


def test_shift_s_opens_the_trust_picker_and_saves_the_choice(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test(size=(100, 20)) as pilot:
            await pilot.pause()
            await pilot.press("S")
            await pilot.pause()
            assert type(app.screen).__name__ == "ChoiceScreen"
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()

    asyncio.run(scenario())
    annotation = store.annotation_for(SYSTEMD)
    assert annotation is not None
    assert annotation.category is Category.SAFE


def test_app_annotations_go_to_the_session_cache(tmp_path: Path) -> None:
    audit = tmp_path / "audit.yaml"
    audit.write_text(
        "version: 1\nannotations:\n  existing|/usr/bin/existing: safe\n",
        encoding="utf-8",
    )
    before = audit.read_text(encoding="utf-8")
    session = tmp_path / "cache" / "session.yaml"
    store = AuditStore.load(audit, session_path=session)
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test(size=(100, 20)) as pilot:
            await pilot.pause()
            await pilot.press("s")
            await pilot.pause()

    asyncio.run(scenario())
    assert audit.read_text(encoding="utf-8") == before
    assert session.exists()


def test_review_screen_lists_the_rules(tmp_path: Path) -> None:
    audit = tmp_path / "audit.yaml"
    audit.write_text(
        "version: 1\nannotations:\n  existing|/usr/bin/existing: safe\n",
        encoding="utf-8",
    )
    session = tmp_path / "cache" / "session.yaml"
    store = AuditStore.load(audit, session_path=session)
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test(size=(100, 20)) as pilot:
            await pilot.pause()
            assert app._store.session_path is not None
            await pilot.press("R")
            await pilot.pause()
            assert type(app.screen).__name__ == "ReviewScreen"

    asyncio.run(scenario())


def test_paper_light_theme_is_the_default(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    app = TopAnnotatorApp(store, scanner=FakeScanner(), refresh_seconds=3600)

    assert app.theme == "paper"
    assert app.current_theme.dark is False


def test_refresh_now_is_available_from_the_command_palette(
    tmp_path: Path,
) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    scanner = FakeScanner()
    app = TopAnnotatorApp(store, scanner=scanner, refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test(size=(100, 20)) as pilot:
            await pilot.pause()
            assert app.frozen
            before = scanner.scans
            await pilot.press("ctrl+p")
            await pilot.press(*"refresh")
            await pilot.press("enter")
            await pilot.pause()
            assert scanner.scans == before + 1
            assert app.frozen

    asyncio.run(scenario())


def test_refresh_keeps_the_scroll_position(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    app = TopAnnotatorApp(store, scanner=ManyScanner(), refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test(size=(100, 20)) as pilot:
            await pilot.pause()
            table = app.query_one(DataTable)
            table.scroll_to(y=8, animate=False, immediate=True)
            await pilot.pause()
            app._scan()
            await pilot.pause()
            assert table.scroll_offset.y == 8

    asyncio.run(scenario())
