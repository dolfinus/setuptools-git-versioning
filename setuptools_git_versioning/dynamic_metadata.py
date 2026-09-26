"""Version provider for the dynamic-metadata protocol."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from setuptools_git_versioning.defaults import set_default_options
from setuptools_git_versioning.setup import read_toml
from setuptools_git_versioning.version import version_from_git

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["dynamic_metadata"]


def dynamic_metadata(
    settings: Mapping[str, Any],
    project: Mapping[str, Any],
) -> dict[str, str]:
    if settings:
        msg = (
            "Inline configuration under [[tool.dynamic-metadata]] is not supported. "
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
            "[tool.setuptools-git-versioning] has 'enabled = false' but the "
            "metadata provider for setuptools-git-versioning was selected. "
            "Either remove the provider or set 'enabled = true'."
        )
        raise ValueError(msg)

    set_default_options(config)

    name = project.get("name")
    package_name = name if isinstance(name, str) else None
    return {"version": str(version_from_git(package_name, **config, root=root))}
