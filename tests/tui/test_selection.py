from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from textual.widgets import DataTable

from top_annotator.audit.routing.os_release import OS_RELEASE_VARIABLE
from top_annotator.core.category import Category
from top_annotator.core.section import Section
from top_annotator.core.section_header import SectionHeader
from top_annotator.core.tree import ProcessRow
from top_annotator.process.scan.demo import DemoMachine
from top_annotator.tui import TopAnnotatorApp

WIREPLUMBER = "wireplumber|/usr/bin/wireplumber"
GSD_COLOR = "gsd-color|/usr/libexec/gsd-color"
PHOTO_INDEXER = "photo-indexer|/opt/photo-indexer/bin/photo-indexer"


def _demo_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TopAnnotatorApp:
    monkeypatch.setenv(OS_RELEASE_VARIABLE, "unset")
    machine = DemoMachine(tmp_path)
    return TopAnnotatorApp(
        machine.store(), scanner=machine.scanner(), refresh_seconds=3600
    )


def _index(app: TopAnnotatorApp, signature: str) -> int:
    return next(
        index
        for index, row in enumerate(app._rows)
        if isinstance(row, ProcessRow)
        and row.process.signature == signature
        and not row.is_context
    )


def test_visual_mode_trusts_every_selected_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _demo_app(tmp_path, monkeypatch)

    async def scenario() -> None:
        async with app.run_test(size=(140, 60)) as pilot:
            await pilot.pause()
            app.query_one(DataTable).move_cursor(row=_index(app, WIREPLUMBER))
            await pilot.press("v")
            app.query_one(DataTable).move_cursor(row=_index(app, GSD_COLOR))
            await pilot.press("s")
            await pilot.pause()

    asyncio.run(scenario())
    for signature in (WIREPLUMBER, GSD_COLOR):
        annotation = app._store.annotation_for(signature)
        assert annotation is not None
        assert annotation.category is Category.TRUST
    assert app._visual_anchor is None


def test_accept_on_a_band_header_takes_every_suggestion_in_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _demo_app(tmp_path, monkeypatch)

    async def scenario() -> None:
        async with app.run_test(size=(140, 60)) as pilot:
            await pilot.pause()
            header = next(
                index
                for index, row in enumerate(app._rows)
                if isinstance(row, SectionHeader)
                and row.section is Section.NEW
                and not row.group
            )
            app.query_one(DataTable).move_cursor(row=header)
            await pilot.press("A")
            await pilot.pause()

    asyncio.run(scenario())
    assert app._store.source_for(PHOTO_INDEXER) == "session"
    assert app._store.annotation_for(WIREPLUMBER) is None
