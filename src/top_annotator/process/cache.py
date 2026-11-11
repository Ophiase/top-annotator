from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

APPLICATION = "top-annotator"
CACHE_VARIABLE = "TOP_ANNOTATOR_CACHE_DIR"
DATA_VARIABLE = "TOP_ANNOTATOR_DATA_DIR"


def default_cache_dir(environment: Mapping[str, str] = os.environ) -> Path:
    return _user_dir(environment, CACHE_VARIABLE, "XDG_CACHE_HOME", ".cache")


def default_data_dir(environment: Mapping[str, str] = os.environ) -> Path:
    """Holds the user's own annotations, so unlike the cache it is never disposable."""
    return _user_dir(environment, DATA_VARIABLE, "XDG_DATA_HOME", ".local/share")


def shown_path(path: Path) -> str:
    home = Path.home()
    return f"~/{path.relative_to(home)}" if path.is_relative_to(home) else str(path)


def _user_dir(
    environment: Mapping[str, str],
    override_variable: str,
    xdg_variable: str,
    home_fallback: str,
) -> Path:
    override = environment.get(override_variable)
    if override:
        return Path(override).expanduser()
    declared = Path(environment.get(xdg_variable, ""))
    base = declared if declared.is_absolute() else Path.home() / home_fallback
    return base / APPLICATION
