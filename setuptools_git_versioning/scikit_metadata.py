"""Dynamic metadata provider for the scikit-build-core build backend."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from setuptools_git_versioning.defaults import set_default_options
from setuptools_git_versioning.setup import read_toml
from setuptools_git_versioning.version import version_from_git

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["dynamic_metadata", "get_requires_for_dynamic_metadata"]


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

    root = Path.cwd()

    config = read_toml(root=root)
    if not config:
        msg = (
            "Missing [tool.setuptools-git-versioning] section in pyproject.toml. "
            "Add it (with at minimum 'enabled = true') to use this provider."
        )
        raise ValueError(msg)

    if not config.pop("enabled", True):
        msg = (
            "[tool.setuptools-git-versioning] has 'enabled = false' but the scikit-build-core "
            "metadata provider for setuptools-git-versioning was selected. "
            "Either remove the provider or set 'enabled = true'."
        )
        raise ValueError(msg)

    set_default_options(config)

    package_name = _read_project_name(root)

    return str(version_from_git(package_name, **config, root=root))


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
