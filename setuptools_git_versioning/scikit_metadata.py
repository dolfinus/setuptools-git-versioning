"""Deprecated version provider for the classic scikit-build-core protocol."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

from setuptools_git_versioning.dynamic_metadata import dynamic_metadata as _dynamic_metadata

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["dynamic_metadata", "get_requires_for_dynamic_metadata"]

warnings.warn(
    "setuptools_git_versioning.scikit_metadata is deprecated; "
    "migrate to [[tool.dynamic-metadata]] with provider = 'setuptools_git_versioning.dynamic_metadata' "
    "on a backend supporting dynamic-metadata such as scikit-build-core>=1.0.",
    DeprecationWarning,
    stacklevel=2,
)


def dynamic_metadata(
    field: str,
    settings: Mapping[str, Any] | None = None,
) -> str:
    if field != "version":
        msg = f"Only the 'version' field is supported, got {field!r}"
        raise ValueError(msg)

    if settings:
        msg = (
            "Inline configuration under [tool.scikit-build.metadata.version] is not supported. "
            "Configure setuptools-git-versioning under [tool.setuptools-git-versioning] instead."
        )
        raise ValueError(msg)

    return _dynamic_metadata({}, {"name": _read_project_name(Path.cwd())})["version"]


def _read_project_name(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return None

    try:
        import tomllib

        with pyproject.open("rb") as file:
            data = tomllib.load(file)
    except ImportError:
        import tomli

        with pyproject.open("rb") as file:
            data = tomli.load(file)

    name = data.get("project", {}).get("name")
    return name if isinstance(name, str) else None


def get_requires_for_dynamic_metadata(
    _settings: Mapping[str, Any] | None = None,
) -> list[str]:
    return ["setuptools-git-versioning"]
