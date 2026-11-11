from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

GIF_WIDTH: Final = 1200
FRAME_DELAY_CENTISECONDS: Final = 15


@dataclass(frozen=True, slots=True)
class GifBuilder:
    frame_dir: Path
    png_dir: Path

    def build(self, destination: Path) -> None:
        self._rasterize()
        destination.parent.mkdir(parents=True, exist_ok=True)
        frames = [str(path) for path in sorted(self.png_dir.glob("*.png"))]
        subprocess.run(
            [
                "convert",
                "-delay",
                str(FRAME_DELAY_CENTISECONDS),
                "-loop",
                "0",
                *frames,
                "-layers",
                "optimize",
                str(destination),
            ],
            check=True,
        )

    def _rasterize(self) -> None:
        import cairosvg  # ty: ignore[unresolved-import]  (supplied by `just gif`)

        self.png_dir.mkdir(parents=True, exist_ok=True)
        for svg in sorted(self.frame_dir.glob("*.svg")):
            cairosvg.svg2png(
                url=str(svg),
                write_to=str(self.png_dir / f"{svg.stem}.png"),
                output_width=GIF_WIDTH,
            )
