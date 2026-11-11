from __future__ import annotations

from typing import ClassVar

from rich.style import Style
from textual.binding import Binding
from textual.widgets import DataTable


class ProcessTable(DataTable):
    """DataTable whose Enter opens the details screen instead of selecting,
    and whose header rows are styled across the full width."""

    BINDINGS: ClassVar = [Binding("enter", "show_detail", "Info")]

    def __init__(self, *, id: str | None = None) -> None:
        super().__init__(id=id)
        self.row_styles: dict[int, Style] = {}

    async def action_show_detail(self) -> None:
        await self.app.run_action("show_detail")

    def _get_row_style(self, row_index: int, base_style: Style) -> Style:
        # Textual's only per-row hook (zebra stripes use it); a cell's own Text
        # style stops at the text, this one also fills the padding.
        style = super()._get_row_style(row_index, base_style)
        extra = self.row_styles.get(row_index)
        return style + extra if extra is not None else style
