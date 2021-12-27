import pytest
import subprocess

from tests.conftest import create_setup_py, get_version


def test_exceptions_wrong_format(repo):
    create_setup_py(repo, [("A", "B")], add=False, commit=False)

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)


def test_exceptions_version_config_false(repo):
    create_setup_py(repo, False, add=False, commit=False)

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)
