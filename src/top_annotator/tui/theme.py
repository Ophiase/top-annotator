from __future__ import annotations

from textual.theme import Theme

PAPER_THEME = Theme(
    name="paper",
    primary="#2f6f6a",
    secondary="#7a5c3e",
    warning="#9a6b1f",
    error="#a33a3a",
    success="#2f7d4e",
    accent="#8a5a44",
    foreground="#2b2a26",
    background="#f6f1e7",
    surface="#fffaf0",
    panel="#e9e1d1",
    boost="#efe7d7",
    dark=False,
    variables={
        "footer-background": "#e9e1d1",
        "footer-key-foreground": "#2f6f6a",
        "input-selection-background": "#2f6f6a 25%",
        "block-cursor-background": "#2f6f6a",
        "block-cursor-foreground": "#fffaf0",
        "block-cursor-text-style": "none",
    },
)
