from __future__ import annotations

import logging
import os
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from secrets import token_hex
from typing import Any, Callable

import tomli_w

log = logging.getLogger(__name__)
root = Path(__file__).parent.parent


def rand_str() -> str:
    return token_hex()


def rand_full_sha() -> str:
    return token_hex(40)


def rand_sha() -> str:
    return token_hex(8)


def execute(cwd: str | os.PathLike, cmd: str, **kwargs) -> str:
    log.info(f"Executing '{cmd}' at '{cwd}'")

    if "env" in kwargs:
        kwargs["env"]["PATH"] = os.environ["PATH"]
        pythonpath = os.getenv("PYTHONPATH", None)
        if pythonpath:
            kwargs["env"]["PYTHONPATH"] = pythonpath

    return subprocess.check_output(cmd, cwd=cwd, shell=True, universal_newlines=True, **kwargs)  # nosec


def get_full_sha(cwd: str | os.PathLike, **kwargs) -> str:
    return execute(cwd, "git rev-list -n 1 HEAD", **kwargs).strip()


def get_sha(cwd: str | os.PathLike, **kwargs) -> str:
    return get_full_sha(cwd, **kwargs)[:8]


def create_commit(
    cwd: str | os.PathLike,
    message: str,
    dt: datetime | None = None,
    **kwargs,
) -> str:
    options = ""

    if dt is not None:
        # Store committer date in case it was set somewhere else
        original_committer_date = os.environ.get("GIT_COMMITTER_DATE", None)

        options += f"--date {dt.isoformat()}"
        # The committer date is what is used to determine sort order for tags, etc
        os.environ["GIT_COMMITTER_DATE"] = dt.isoformat()

    try:
        return_value = execute(cwd, f'git commit -m "{message}" {options}', **kwargs)
    finally:
        # Return committer date env var to prior value if set
        if dt is not None:
            if original_committer_date is None:
                # unset the var
                del os.environ["GIT_COMMITTER_DATE"]
            else:
                # restore previous value
                os.environ["GIT_COMMITTER_DATE"] = original_committer_date

    return return_value


def create_tag(
    cwd: str | os.PathLike,
    tag: str,
    message: str | None = None,
    commit: str | None = None,
    **kwargs,
) -> str:
    options = ""
    if message:
        options += f' -a -m "{message}"'

    if not commit:
        commit = ""

    return execute(cwd, f"git tag {options} {tag} {commit}", **kwargs)


def checkout_branch(cwd: str | os.PathLike, branch: str, new: bool = True, **kwargs) -> str:
    options = ""
    if new:
        options += " -b"
    return execute(cwd, f"git checkout {options} {branch}", **kwargs)


def create_folder(
    cwd: str | os.PathLike,
    name: str | None = None,
    add: bool = True,
    commit: bool = True,
    **kwargs,
) -> str | None:
    result = None
    if not name:
        name = rand_str()

    path = Path(cwd).joinpath(name)

    # create dir with some random file
    path.mkdir(parents=True, exist_ok=True)
    path.joinpath(rand_str()).touch()

    if add:
        execute(cwd, f"git add {name}")
        log.info(execute(cwd, "git status"))
        log.info(execute(cwd, "git diff"))

        if commit:
            create_commit(cwd, f"Add {name}")
            result = get_sha(cwd)

    return result


def create_file(
    cwd: str | os.PathLike,
    name: str | None = None,
    content: str | None = None,
    add: bool = True,
    commit: bool = True,
    **kwargs,
) -> str | None:
    result = None

    if not name:
        name = rand_str()
    if content is None:
        content = rand_str()

    log.info(content)
    Path(cwd).joinpath(name).write_text(content)

    if add:
        execute(cwd, f"git add {name}")
        log.info(execute(cwd, "git status"))
        log.info(execute(cwd, "git diff"))

        if commit:
            create_commit(cwd, f"Add {name}")
            result = get_sha(cwd)

    return result


def create_pyproject_toml(
    cwd: str | os.PathLike,
    config: dict | None = None,
    commit: bool = True,
    **kwargs,
) -> str | None:
    # well, using pyproject.toml+setup.cfg is more classic
    # but it is not easy to check code coverage in such a case
    # so we're using pyproject.toml+setup.py
    create_file(
        cwd,
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
        commit=False,
        **kwargs,
    )

    cfg: dict[str, Any] = {}
    cfg["build-system"] = {
        "requires": [
            "setuptools>=41",
            "wheel",
            "setuptools-git-versioning",
            "coverage",
        ],
        # with default "setuptools.build_meta" it is not possible to build package
        # which uses its own source code to get version number,
        # e.g. `version_callback` or `branch_formatter`
        # mote details: https://github.com/pypa/setuptools/issues/1642#issuecomment-457673563
        "build-backend": "setuptools.build_meta:__legacy__",
    }

    if config is None:
        config = {"enabled": True}

    if config != NotImplemented:
        cfg["tool"] = {"setuptools-git-versioning": config}

    return create_file(cwd, "pyproject.toml", tomli_w.dumps(cfg), commit=commit, **kwargs)


def create_setup_py(
    cwd: str | os.PathLike,
    config: dict | None = None,
    **kwargs,
) -> str | None:
    if config is None:
        config = {"enabled": True}

    if config == NotImplemented:
        cfg = ""
    else:
        cfg = f"setuptools_git_versioning={config},"

    return create_file(
        cwd,
        "setup.py",
        textwrap.dedent(
            f"""
            from coverage.control import Coverage

            coverage = Coverage()
            coverage.start()

            try:
                import setuptools

                setuptools.setup(
                    name="mypkg",
                    {cfg}
                    setup_requires=[
                        "setuptools>=41",
                        "wheel",
                        "coverage",
                        "setuptools-git-versioning",
                    ]
                )
            finally:
                coverage.stop()
                coverage.save()
            """
        ),
        **kwargs,
    )


def typed_config(
    repo: str | os.PathLike,
    config_creator: Callable,
    config_type: str,
    template: str | None = None,
    template_name: str | None = None,
    config: dict | None = None,
) -> None:
    if config_type == "tag":
        cfg = {}
    else:
        cfg = {"version_file": "VERSION.txt", "count_commits_from_version_file": True}

    if template_name is None:
        if config_type == "tag":
            template_name = "template"
        else:
            template_name = "dev_template"

    if template:
        cfg[template_name] = template

    if config:
        cfg.update(config)

    config_creator(repo, cfg)

    if config_type == "tag":
        create_tag(repo, "1.2.3")
    else:
        create_file(repo, "VERSION.txt", "1.2.3")


def get_version_setup_py(cwd: str | os.PathLike, **kwargs) -> str:
    return execute(cwd, f"{sys.executable} setup.py --version", **kwargs).strip()


def get_version_module(cwd: str | os.PathLike, args: list[str] | None = None, **kwargs) -> str:
    args_str = " ".join(args or [])

    return execute(
        cwd,
        f"{sys.executable} -m coverage run -m setuptools_git_versioning {args_str} -vv",
        **kwargs,
    ).strip()


def get_version_script(cwd: str | os.PathLike, args: list[str] | None = None, **kwargs) -> str:
    args_str = " ".join(args or [])
    return execute(cwd, f"setuptools-git-versioning {args_str} -vv", **kwargs).strip()


def get_version(cwd: str | os.PathLike, isolated: bool = False, **kwargs) -> str:
    cmd = f"{sys.executable} -m build -s"
    if not isolated:
        cmd += " --no-isolation"
    execute(cwd, cmd, **kwargs)

    content = Path(cwd).joinpath("mypkg.egg-info/PKG-INFO").read_text().splitlines()

    for line in content:
        if line.startswith("Version: "):
            return line.replace("Version: ", "").strip()

    raise RuntimeError("Cannot get package version")
