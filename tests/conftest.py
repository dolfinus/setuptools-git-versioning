import logging
import os
import pytest
import subprocess
import sys
import textwrap
import uuid

from typing import Any, Optional

try:
    from shlex import quote as cmd_quote
except ImportError:
    from pipes import quote as cmd_quote

log = logging.getLogger(__name__)


def rand_str():  # type: () -> str
    return str(uuid.uuid4())


def execute(cwd, cmd, **kwargs):  # type: (str, str, **Any) -> str
    log.info(cwd)
    return subprocess.check_output(cmd, cwd=cwd, shell=True, universal_newlines=True, **kwargs)  # nosec


def create_file(
    cwd, name=None, content=None, add=True, commit=True
):  # type: (str, Optional[str], Optional[str], bool, bool) -> Optional[str]
    result = None

    if not name:
        name = rand_str()
    if content is None:
        content = rand_str()
    with open(os.path.join(cwd, name), "w") as f:
        f.write(content)

    if add:
        execute(cwd, "git add {name}".format(name=cmd_quote(name)))

        if commit:
            msg = "Add {}".format(name)
            execute(cwd, "git commit -m {msg}".format(msg=cmd_quote(msg)))
            result = get_short_commit(cwd)

    log.info(execute(cwd, "git status"))
    log.info(execute(cwd, "git diff"))
    return result


def create_setup_py(cwd, config=None, **kwargs):  # type: (str, Optional[dict], **Any) -> Optional[str]
    return create_file(
        cwd,
        "setup.py",
        textwrap.dedent(
            """
            import setuptools
            setuptools.setup(
                version_config={config},
                setup_requires=["setuptools-git-versioning"]
            )
        """
        ).format(config=config or True),
        **kwargs
    )


def get_version(cwd, **kwargs):  # type: (str, **Any) -> str
    return execute(cwd, "{python} setup.py --version".format(python=sys.executable), **kwargs).strip()


def get_commit(cwd, **kwargs):  # type: (str, **Any) -> str
    return execute(cwd, "git rev-list -n 1 HEAD", **kwargs).strip()


def get_short_commit(cwd, **kwargs):  # type: (str, *Any) -> str
    return get_commit(cwd, **kwargs)[:8]


@pytest.fixture
def repo(tmpdir):
    repo_dir = str(tmpdir.mkdir(rand_str()))
    execute(repo_dir, "git init -b master")
    create_file(
        repo_dir,
        ".gitignore",
        textwrap.dedent(
            """
        .eggs
        _build
        dist
        *.py[oc]
    """
        ),
    )
    return repo_dir