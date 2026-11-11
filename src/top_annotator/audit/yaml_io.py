from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import yaml

from ..core.annotation import FLAGS, Annotation
from ..core.category import LEGACY_PROVIDERS, Category

CACHE_FILENAME = "audit"
CACHE_SUFFIXES = {".yaml", ".yml"}
BASE_AUDIT = Path(__file__).parent / "base"
BASE_VARIABLE = "TOP_ANNOTATOR_AUDIT"
SUGGESTIONS_FOLDER = "suggestions"


def default_audit_path(environment: Mapping[str, str] = os.environ) -> Path:
    override = environment.get(BASE_VARIABLE)
    return Path(override).expanduser() if override else BASE_AUDIT


def cache_header(family: str, *, shareable: bool = True) -> str:
    scope = "safe to edit and share" if shareable else "local session cache"
    return (
        f"# top-annotator cache ({family}); {scope}.\n"
        "# Signature = process name | executable (or argv[0]) [| script].\n"
    )


def cache_files(path: Path, scopes: tuple[str, ...] = ()) -> tuple[Path, ...]:
    """Every audit file under `path`. A folder split by distribution (it has
    a `common/`) contributes only the subfolders named in `scopes`."""
    return tuple(
        file for file in _yaml_files(path, scopes) if not _suggests(file, path)
    )


def suggestion_files(path: Path, scopes: tuple[str, ...] = ()) -> tuple[Path, ...]:
    """The files under a `suggestions/` folder: entries offered, never trusted."""
    return tuple(file for file in _yaml_files(path, scopes) if _suggests(file, path))


def _suggests(file: Path, root: Path) -> bool:
    return SUGGESTIONS_FOLDER in file.relative_to(root).parts


def _yaml_files(path: Path, scopes: tuple[str, ...]) -> tuple[Path, ...]:
    if path.is_dir():
        roots = [path]
        if scopes and (path / scopes[0]).is_dir():
            roots = [path / scope for scope in scopes if (path / scope).is_dir()]
        return tuple(
            sorted(
                file
                for root in roots
                for file in (*root.rglob("*.yaml"), *root.rglob("*.yml"))
            )
        )
    if path.suffix in CACHE_SUFFIXES:
        return (path,)
    return ()


def read_annotations(path: Path) -> dict[str, Annotation]:
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError, yaml.YAMLError:
        return {}
    if not isinstance(payload, dict):
        return {}
    raw_annotations = payload.get("annotations")
    if not isinstance(raw_annotations, dict):
        return {}
    loaded: dict[str, Annotation] = {}
    for signature, raw in raw_annotations.items():
        annotation = parse_annotation(raw)
        if annotation is not None:
            loaded[str(signature)] = annotation
    return loaded


def write_annotations(
    path: Path,
    annotations: dict[str, Annotation],
    *,
    shareable: bool = True,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "annotations": {
            signature: entry_of(annotation)
            for signature, annotation in sorted(annotations.items())
        },
    }
    body = yaml.safe_dump(
        payload,
        allow_unicode=True,
        sort_keys=True,
        width=100,
    )
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        cache_header(path.stem, shareable=shareable) + body,
        encoding="utf-8",
    )
    temporary.replace(path)


def entry_of(annotation: Annotation) -> dict[str, object]:
    entry: dict[str, object] = {
        "category": annotation.category.value,
        "note": annotation.note,
        "updated": annotation.updated.isoformat(),
    }
    if annotation.provider:
        entry["provider"] = annotation.provider
    if annotation.children is not None:
        entry["children"] = list(annotation.children)
    entry.update({flag: True for flag, value in annotation.flags().items() if value})
    if annotation.agents:
        entry["agents"] = list(annotation.agents)
    if annotation.plugin_args:
        entry["plugin_args"] = list(annotation.plugin_args)
    return entry


def parse_annotation(raw: object) -> Annotation | None:
    if isinstance(raw, str):
        return _annotation_from_category(raw)
    if not isinstance(raw, dict):
        return None
    annotation = _annotation_from_category(str(raw.get("category", "")))
    if annotation is None:
        return None
    return Annotation(
        category=annotation.category,
        note=str(raw.get("note", "")),
        provider=_parse_provider(raw.get("provider")),
        updated=_parse_date(raw.get("updated")),
        children=_parse_children(raw.get("children")),
        agents=_parse_children(raw.get("agents")) or (),
        plugin_args=_parse_children(raw.get("plugin_args")) or (),
        **{flag: raw.get(flag) is True for flag in FLAGS},
    )


def _parse_children(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        return None
    return tuple(str(name) for name in value)


def _annotation_from_category(value: str) -> Annotation | None:
    try:
        return Annotation(category=Category(value))
    except ValueError:
        return None


def _parse_date(value: object) -> date:
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return date.today()


def _parse_provider(value: object) -> str:
    provider = str(value or "")
    return LEGACY_PROVIDERS.get(provider, provider)
