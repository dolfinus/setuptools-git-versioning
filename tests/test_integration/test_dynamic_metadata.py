from __future__ import annotations

import re
import sys
import textwrap
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import pytest
import tomli_w

from setuptools_git_versioning import dynamic_metadata as metadata
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

    assert metadata.dynamic_metadata({}, {"name": "mypkg"})["version"] == "0.0.1"


def test_tagged_repo_returns_tag(repo, monkeypatch):
    write_config(repo, {"enabled": True})
    create_tag(repo, "1.2.3")
    monkeypatch.chdir(repo)

    assert metadata.dynamic_metadata({}, {"name": "mypkg"})["version"] == "1.2.3"


def test_dev_template_used_after_tag(repo, monkeypatch):
    write_config(repo, {"enabled": True})
    create_tag(repo, "1.2.3")
    create_file(repo, "extra.txt", "extra")
    monkeypatch.chdir(repo)

    result = metadata.dynamic_metadata({}, {"name": "mypkg"})["version"]
    assert re.fullmatch(r"1\.2\.3\.post1\+git\.[0-9a-f]{8}", result), result


def test_rejects_missing_section(repo, monkeypatch):
    # pyproject.toml exists but has no [tool.setuptools-git-versioning] section
    create_file(repo, "pyproject.toml", textwrap.dedent('[project]\nname = "mypkg"\n'))
    monkeypatch.chdir(repo)

    with pytest.raises(ValueError, match=r"Missing \[tool\.setuptools-git-versioning\]"):
        metadata.dynamic_metadata({}, {"name": "mypkg"})["version"]


def test_rejects_enabled_false(repo, monkeypatch):
    write_config(repo, {"enabled": False})
    monkeypatch.chdir(repo)

    with pytest.raises(ValueError, match="enabled = false"):
        metadata.dynamic_metadata({}, {"name": "mypkg"})["version"]


def test_registered_provider(repo, monkeypatch):
    importlib_metadata = pytest.importorskip("importlib.metadata")
    write_config(repo, {"enabled": True})
    create_tag(repo, "1.2.3")
    monkeypatch.chdir(repo)

    entry_points = [
        entry
        for entry in importlib_metadata.distribution("setuptools-git-versioning").entry_points
        if entry.group == "dynamic_metadata.provider" and entry.name == "setuptools_git_versioning.dynamic_metadata"
    ]
    (entry_point,) = entry_points
    provider = entry_point.load()
    settings = MappingProxyType({})
    project = MappingProxyType({"name": "mypkg", "dynamic": ["version"]})

    assert provider.dynamic_metadata(settings=settings, project=project) == {"version": "1.2.3"}
    assert project == {"name": "mypkg", "dynamic": ["version"]}


@pytest.mark.skipif(sys.version_info < (3, 8), reason="dynamic-metadata requires Python 3.8+")
@pytest.mark.parametrize("build_state", ["sdist", "wheel", "editable", "metadata_wheel", "metadata_editable"])
def test_dynamic_metadata_loader(repo, monkeypatch, build_state):
    from dynamic_metadata.loader import (
        dynamic_wheel_fields,
        entries_from_pyproject,
        get_requires_for_dynamic_metadata,
        process_dynamic_metadata,
    )

    config = {
        "project": {"name": "mypkg", "dynamic": ["version", "description"]},
        "tool": {
            "setuptools-git-versioning": {"enabled": True},
            "dynamic-metadata": [
                {"provider": "setuptools_git_versioning.dynamic_metadata"},
                {
                    "provider": "dynamic_metadata.template",
                    "field": "description",
                    "result": "{project[name]} {project[version]}",
                },
            ],
        },
    }
    create_file(repo, "pyproject.toml", tomli_w.dumps(config))
    create_tag(repo, "1.2.3")
    monkeypatch.chdir(repo)

    entries = entries_from_pyproject(config)
    assert process_dynamic_metadata(config["project"], entries, build_state) == {
        "name": "mypkg",
        "version": "1.2.3",
        "description": "mypkg 1.2.3",
        "dynamic": [],
    }
    assert dynamic_wheel_fields(entries) == set()
    assert get_requires_for_dynamic_metadata(entries) == []


def test_dynamic_metadata_uses_resolved_project_name(repo, monkeypatch):
    write_config(repo, {"enabled": True, "version_callback": ".version:get_version"})
    (repo / "resolved_pkg").mkdir()
    create_file(repo, "resolved_pkg/__init__.py", "")
    create_file(repo, "resolved_pkg/version.py", 'def get_version():\n    return "2.3.4"\n')
    monkeypatch.chdir(repo)

    assert metadata.dynamic_metadata({}, {"name": "resolved_pkg"}) == {"version": "2.3.4"}


def test_dynamic_metadata_without_project_name(repo, monkeypatch):
    write_config(repo, {"enabled": True, "starting_version": "2.0"})
    monkeypatch.chdir(repo)

    assert metadata.dynamic_metadata({}, {}) == {"version": "2.0"}


def test_dynamic_metadata_rejects_inline_settings(repo, monkeypatch):
    write_config(repo, {"enabled": True})
    monkeypatch.chdir(repo)
    settings = MappingProxyType({"template": "{tag}"})

    with pytest.raises(ValueError, match=r"Inline configuration under \[\[tool\.dynamic-metadata\]\]"):
        metadata.dynamic_metadata(settings, {"name": "mypkg"})

    assert settings == {"template": "{tag}"}


def test_version_file(repo, monkeypatch):
    write_config(repo, {"enabled": True, "version_file": "VERSION"})
    create_file(repo, "VERSION", "3.4.5")
    monkeypatch.chdir(repo)

    assert metadata.dynamic_metadata({}, {"name": "mypkg"})["version"] == "3.4.5"


def test_sdist_version_is_preserved(repo_dir, monkeypatch):
    (repo_dir / "pyproject.toml").write_text("[tool.setuptools-git-versioning]\nenabled = true\n")
    (repo_dir / "PKG-INFO").write_text("Metadata-Version: 2.2\nName: mypkg\nVersion: 4.5.6\n")
    monkeypatch.chdir(repo_dir)

    assert metadata.dynamic_metadata({}, {"name": "mypkg"})["version"] == "4.5.6"


def test_end_to_end_build_via_scikit_build_core(repo):
    """Build using the new dynamic-metadata provider."""
    import scikit_build_core
    from packaging.version import Version

    if Version(scikit_build_core.__version__) < Version("1.0"):
        pytest.skip("The tool.dynamic-metadata configuration requires scikit-build-core 1.0+")

    config = {
        "setuptools-git-versioning": {"enabled": True},
        "dynamic-metadata": [{"provider": "setuptools_git_versioning.dynamic_metadata"}],
    }
    requirements = ["scikit-build-core", "setuptools-git-versioning", "dynamic-metadata>=0.4"]

    create_file(
        repo,
        "pyproject.toml",
        tomli_w.dumps(
            {
                "build-system": {
                    "requires": requirements,
                    "build-backend": "scikit_build_core.build",
                },
                "project": {"name": "mypkg", "dynamic": ["version"]},
                "tool": config,
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
