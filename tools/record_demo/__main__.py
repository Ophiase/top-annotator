import asyncio
import sys
import tempfile
from pathlib import Path

from .frame_recorder import FrameRecorder
from .gif_builder import GifBuilder


def main() -> None:
    destination = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/media/demo.gif")
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        frame_dir = root / "frames"
        frame_dir.mkdir()
        frames = asyncio.run(FrameRecorder(frame_dir).record())
        GifBuilder(frame_dir, root / "png").build(destination)
    print(f"{frames} frames -> {destination}")


main()
