from __future__ import annotations

from pathlib import Path

from top_annotator.process.cache import (
    default_cache_dir,
    default_data_dir,
    shown_path,
)


def test_override_wins() -> None:
    environment = {
        "TOP_ANNOTATOR_CACHE_DIR": "/srv/audit-cache",
        "XDG_CACHE_HOME": "/xdg",
    }
    assert default_cache_dir(environment) == Path("/srv/audit-cache")


def test_xdg_cache_home() -> None:
    assert default_cache_dir({"XDG_CACHE_HOME": "/xdg"}) == Path("/xdg/top-annotator")


def test_falls_back_to_home_cache() -> None:
    assert default_cache_dir({}) == Path.home() / ".cache" / "top-annotator"


def test_relative_xdg_is_ignored() -> None:
    expected = Path.home() / ".cache" / "top-annotator"
    assert default_cache_dir({"XDG_CACHE_HOME": "relative"}) == expected


def test_data_dir_override_wins() -> None:
    environment = {"TOP_ANNOTATOR_DATA_DIR": "/srv/mine", "XDG_DATA_HOME": "/xdg"}
    assert default_data_dir(environment) == Path("/srv/mine")


def test_data_dir_follows_xdg_data_home() -> None:
    assert default_data_dir({"XDG_DATA_HOME": "/xdg"}) == Path("/xdg/top-annotator")


def test_data_dir_is_not_the_cache() -> None:
    expected = Path.home() / ".local" / "share" / "top-annotator"
    assert default_data_dir({}) == expected


def test_shown_path_abbreviates_home() -> None:
    assert shown_path(Path.home() / "a" / "b") == "~/a/b"
    assert shown_path(Path("/srv/audit")) == "/srv/audit"
