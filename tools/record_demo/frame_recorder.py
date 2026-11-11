from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Final

from textual.pilot import Pilot

from top_annotator.process.scan.demo import DEMO_NOTICE, DemoMachine
from top_annotator.tui import TopAnnotatorApp

TERMINAL_SIZE: Final = (132, 40)
FAKE_SSHD_PID: Final = 802
UNANNOTATED_PID: Final = 1750


class FrameRecorder:
    """Drives the TUI headlessly on the demo machine, one SVG per frame."""

    def __init__(self, frame_dir: Path) -> None:
        self._frame_dir = frame_dir
        self._index = 0

    async def record(self) -> int:
        with tempfile.TemporaryDirectory() as scratch:
            machine = DemoMachine(Path(scratch))
            app = TopAnnotatorApp(
                machine.store(),
                scanner=machine.scanner(),
                notice=DEMO_NOTICE,
            )
            async with app.run_test(size=TERMINAL_SIZE) as pilot:
                await self._play(app, pilot)
        return self._index

    async def _play(self, app: TopAnnotatorApp, pilot: Pilot[None]) -> None:
        await self._capture(app, pilot, hold=14)
        await self._walk_to(app, pilot, FAKE_SSHD_PID)
        await pilot.press("enter")
        if len(app.screen_stack) <= 1:
            raise RuntimeError("the details screen did not open")
        await self._capture(app, pilot, hold=16)
        await pilot.press("escape")
        await self._walk_to(app, pilot, UNANNOTATED_PID)
        await self._capture(app, pilot, hold=6)
        await pilot.press("A")
        await self._capture(app, pilot, hold=10)
        await pilot.press("u")
        await self._capture(app, pilot, hold=6)
        await pilot.press("slash")
        for key in "zsh":
            await pilot.press(key)
            await self._capture(app, pilot, hold=2)
        await self._capture(app, pilot, hold=14)

    async def _walk_to(
        self, app: TopAnnotatorApp, pilot: Pilot[None], pid: int
    ) -> None:
        """One `j` per frame, so the cursor is seen travelling down the tree."""
        for _ in range(len(app._rows)):
            if app._selected_pid() == pid:
                return
            await pilot.press("j")
            await self._capture(app, pilot)
        raise RuntimeError(f"process {pid} is not on screen")

    async def _capture(
        self, app: TopAnnotatorApp, pilot: Pilot[None], hold: int = 1
    ) -> None:
        """`hold` repeats the frame, which is how a still moment is timed."""
        await pilot.pause()
        screenshot = app.export_screenshot()
        for _ in range(hold):
            (self._frame_dir / f"{self._index:03d}.svg").write_text(screenshot)
            self._index += 1
