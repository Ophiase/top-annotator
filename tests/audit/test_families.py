from __future__ import annotations

from top_annotator.audit import COSMIC, GNOME, family_for

from ..factories import process


def test_cosmic_name_routes_to_cosmic() -> None:
    panel = process(10, 1, name="cosmic-panel", exe="/usr/bin/cosmic-panel")
    assert family_for(panel) == COSMIC


def test_cosmic_portal_is_not_gnome() -> None:
    portal = process(
        11,
        1,
        name="xdg-desktop-por",
        exe="/usr/libexec/xdg-desktop-portal-cosmic",
    )
    assert family_for(portal) == COSMIC


def test_gnome_portal_stays_gnome() -> None:
    portal = process(
        12, 1, name="xdg-desktop-por", exe="/usr/libexec/xdg-desktop-portal"
    )
    assert family_for(portal) == GNOME
