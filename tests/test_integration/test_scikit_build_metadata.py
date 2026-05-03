from __future__ import annotations

import re
import sys
import textwrap
from typing import TYPE_CHECKING, Any

import pytest
import tomli_w

from setuptools_git_versioning import scikit_metadata as metadata
from tests.lib.util import create_file, create_tag, execute

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.all, pytest.mark.important]


def write_config(repo: Path, config: dict[str, Any] | None) -> None:
    """Write a pyproject.toml with only the [tool.setuptools-git-versioning] section we need."""
    cfg: dict[str, Any] = {"project": {"name": "mypkg", "dynamic": ["version"]}}
    if config is not None:
        cfg["tool"] = {"setuptools-git-versioning": config}
    create_file(repo, "pyproject.toml", tomli_w.dumps(cfg))


def test_untagged_repo_returns_starting_version(repo, monkeypatch):
    write_config(repo, {"enabled": True})
    monkeypatch.chdir(repo)

    assert metadata.dynamic_metadata("version") == "0.0.1"


def test_tagged_repo_returns_tag(repo, monkeypatch):
    write_config(repo, {"enabled": True})
    create_tag(repo, "1.2.3")
    monkeypatch.chdir(repo)

    assert metadata.dynamic_metadata("version") == "1.2.3"


def test_dev_template_used_after_tag(repo, monkeypatch):
    write_config(repo, {"enabled": True})
    create_tag(repo, "1.2.3")
    create_file(repo, "extra.txt", "extra")
    monkeypatch.chdir(repo)

    result = metadata.dynamic_metadata("version")
    assert re.fullmatch(r"1\.2\.3\.post1\+git\.[0-9a-f]{8}", result), result


def test_reads_project_name_from_pyproject(repo, monkeypatch):
    write_config(repo, {"enabled": True})
    monkeypatch.chdir(repo)

    captured: dict[str, Any] = {}

    def fake_version_from_git(package_name=None, **_kwargs):
        from packaging.version import Version

        captured["package_name"] = package_name
        return Version("9.9.9")

    monkeypatch.setattr(metadata, "version_from_git", fake_version_from_git)

    assert metadata.dynamic_metadata("version") == "9.9.9"
    assert captured["package_name"] == "mypkg"


def test_no_project_section_means_no_package_name(repo, monkeypatch):
    create_file(
        repo,
        "pyproject.toml",
        tomli_w.dumps({"tool": {"setuptools-git-versioning": {"enabled": True}}}),
    )
    monkeypatch.chdir(repo)

    captured: dict[str, Any] = {}

    def fake_version_from_git(package_name=None, **_kwargs):
        from packaging.version import Version

        captured["package_name"] = package_name
        return Version("0.0.1")

    monkeypatch.setattr(metadata, "version_from_git", fake_version_from_git)

    metadata.dynamic_metadata("version")
    assert captured["package_name"] is None


def test_rejects_non_version_field(repo, monkeypatch):
    write_config(repo, {"enabled": True})
    monkeypatch.chdir(repo)

    with pytest.raises(ValueError, match="Only the 'version' field"):
        metadata.dynamic_metadata("description")


def test_rejects_inline_settings(repo, monkeypatch):
    write_config(repo, {"enabled": True})
    monkeypatch.chdir(repo)

    with pytest.raises(ValueError, match="Inline configuration"):
        metadata.dynamic_metadata("version", {"template": "{tag}"})


def test_rejects_missing_section(repo, monkeypatch):
    # pyproject.toml exists but has no [tool.setuptools-git-versioning] section
    create_file(repo, "pyproject.toml", textwrap.dedent('[project]\nname = "mypkg"\n'))
    monkeypatch.chdir(repo)

    with pytest.raises(ValueError, match=r"Missing \[tool\.setuptools-git-versioning\]"):
        metadata.dynamic_metadata("version")


def test_rejects_enabled_false(repo, monkeypatch):
    write_config(repo, {"enabled": False})
    monkeypatch.chdir(repo)

    with pytest.raises(ValueError, match="enabled = false"):
        metadata.dynamic_metadata("version")


def test_get_requires_for_dynamic_metadata():
    assert metadata.get_requires_for_dynamic_metadata() == ["setuptools-git-versioning"]
    assert metadata.get_requires_for_dynamic_metadata({"anything": True}) == ["setuptools-git-versioning"]


def test_end_to_end_build_via_scikit_build_core(repo):
    """Drive the actual scikit-build-core backend to verify the provider protocol matches."""

    create_file(
        repo,
        "pyproject.toml",
        tomli_w.dumps(
            {
                "build-system": {
                    "requires": ["scikit-build-core", "setuptools-git-versioning"],
                    "build-backend": "scikit_build_core.build",
                },
                "project": {"name": "mypkg", "dynamic": ["version"]},
                "tool": {
                    "scikit-build": {
                        "experimental": True,
                        "metadata": {
                            "version": {"provider": "setuptools_git_versioning.scikit_metadata"},
                        },
                    },
                    "setuptools-git-versioning": {"enabled": True},
                },
            },
        ),
    )
    create_file(
        repo,
        "CMakeLists.txt",
        textwrap.dedent(
            """
            cmake_minimum_required(VERSION 3.15)
            project(mypkg LANGUAGES NONE)
            install(FILES mypkg/__init__.py DESTINATION mypkg)
            """,
        ),
    )
    (repo / "mypkg").mkdir()
    create_file(repo, "mypkg/__init__.py", "")
    create_tag(repo, "1.2.3")

    execute(repo, sys.executable, "-m", "build", "--sdist", "--no-isolation")

    sdists = list((repo / "dist").glob("mypkg-*.tar.gz"))
    assert len(sdists) == 1, sdists
    assert sdists[0].name == "mypkg-1.2.3.tar.gz"
