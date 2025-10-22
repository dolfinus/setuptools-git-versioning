import os
import subprocess
import textwrap

import pytest
import tomli_w

from tests.lib.util import (
    create_file,
    create_folder,
    create_pyproject_toml,
    create_setup_py,
    get_version,
    get_version_module,
    get_version_script,
    get_version_setup_py,
)

pytestmark = [pytest.mark.all, pytest.mark.important]


def test_config_not_set(repo, create_config):
    # legacy builder for pyproject.toml
    create_config(repo, NotImplemented)

    assert get_version(repo) == "0.0.0"


def test_config_not_used(repo):
    # modern builder for pyproject.toml
    create_file(
        repo,
        "setup.py",
        textwrap.dedent(
            """
            from coverage.control import Coverage

            coverage = Coverage()
            coverage.start()

            try:
                import setuptools

                setuptools.setup(
                    name="mypkg",
                )
            finally:
                coverage.stop()
                coverage.save()
            """
        ),
    )
    assert get_version_setup_py(repo) == "0.0.0"

    cfg = {
        "build-system": {
            "requires": [
                "setuptools>=41",
                "wheel",
                "coverage",
            ],
            "build-backend": "setuptools.build_meta",
        }
    }

    create_file(
        repo,
        "pyproject.toml",
        tomli_w.dumps(cfg),
    )

    assert get_version(repo, isolated=False) == "0.0.0"
    assert get_version(repo, isolated=True) == "0.0.0"

    # python -m setuptools_git_versioning
    # and
    # setuptools-git-versioning
    # requires pyproject.toml or setup.py to exist with `enabled: True`` option
    with pytest.raises(subprocess.CalledProcessError):
        get_version_module(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_script(repo)


def test_config_enabled_true(repo, create_config):
    create_config(repo, {"enabled": True})

    assert get_version(repo) == "0.0.1"
    assert get_version_script(repo) == "0.0.1"
    assert get_version_module(repo) == "0.0.1"

    # path to the repo can be passed as positional argument
    assert get_version_script(os.getcwd(), args=[repo]) == "0.0.1"
    assert get_version_module(os.getcwd(), args=[repo]) == "0.0.1"


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        [("A", "B")],
    ],
)
def test_config_wrong_format(repo, create_config, value):
    create_config(repo, value)

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_module(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_script(repo)


def test_config_pyproject_toml_is_used_then_setup_py_is_empty(repo):
    create_pyproject_toml(repo, {"starting_version": "2.3.4"}, add=False, commit=False)
    create_setup_py(repo, NotImplemented, add=False, commit=False)

    assert get_version(repo) == "2.3.4"
    assert get_version_script(repo) == "2.3.4"
    assert get_version_module(repo) == "2.3.4"


def test_config_pyproject_toml_is_used_then_setup_py_does_not_exist(repo):
    create_pyproject_toml(repo, {"starting_version": "2.3.4"}, add=False, commit=False)
    create_file(
        repo,
        "setup.cfg",
        textwrap.dedent(
            """
            [metadata]
            name = mypkg
            """
        ),
    )

    assert get_version(repo) == "2.3.4"
    assert get_version_script(repo) == "2.3.4"
    assert get_version_module(repo) == "2.3.4"


def test_config_setup_py_is_used_then_pyproject_toml_is_empty(repo):
    create_pyproject_toml(repo, NotImplemented, add=False, commit=False)
    create_setup_py(repo, {"starting_version": "2.3.4"}, add=False, commit=False)

    assert get_version(repo) == "2.3.4"
    assert get_version_setup_py(repo) == "2.3.4"
    assert get_version_module(repo) == "2.3.4"
    assert get_version_script(repo) == "2.3.4"


def test_config_setup_py_is_used_then_pyproject_toml_does_not_exist(repo):
    create_setup_py(repo, {"starting_version": "2.3.4"}, add=False, commit=False)

    assert get_version(repo) == "2.3.4"
    assert get_version_setup_py(repo) == "2.3.4"
    assert get_version_module(repo) == "2.3.4"
    assert get_version_script(repo) == "2.3.4"


def test_config_both_setup_py_and_pyproject_toml_are_present(repo):
    create_pyproject_toml(repo)
    create_setup_py(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_setup_py(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_script(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_module(repo)


def test_config_setup_py_is_folder(repo):
    create_folder(repo, "setup.py")

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_module(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_script(repo)


def test_config_pyproject_toml_is_folder(repo):
    create_folder(repo, "pyproject.toml")

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_module(repo)

    with pytest.raises(subprocess.CalledProcessError):
        get_version_script(repo)
