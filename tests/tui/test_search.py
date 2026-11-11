from __future__ import annotations

import asyncio
from pathlib import Path

from top_annotator.audit import AuditStore
from top_annotator.tui import TopAnnotatorApp

from .many_scanner import ManyScanner


def test_typing_in_search_filters_the_rows(tmp_path: Path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    app = TopAnnotatorApp(store, scanner=ManyScanner(), refresh_seconds=3600)

    async def scenario() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            before = len(app._rows)
            await pilot.press("slash", "z", "z", "z", "q")
            await pilot.pause()
            assert app._query == "zzzq"
            assert len(app._rows) < before

    asyncio.run(scenario())
