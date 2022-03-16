import logging
import os
import subprocess
import sys
import textwrap
import toml

from datetime import datetime
from typing import Any, Callable, Dict, Optional

try:
    from secrets import token_hex
except ImportError:
    # TODO: remove after dropping Python 2.7 and 3.5 support
    import string
    import random

    def token_hex(nbytes=None):  # type: (Optional[int]) -> str
        size = nbytes * 2 if nbytes is not None else 64
        return "".join(random.choice(string.hexdigits) for i in range(size)).lower()


log = logging.getLogger(__name__)
root = os.path.dirname(os.path.dirname(__file__))


def rand_str():  # type: () -> str
    return token_hex()


def rand_full_sha():  # type: () -> str
    return token_hex(40)


def rand_sha():  # type: () -> str
    return token_hex(8)


def execute(cwd, cmd, **kwargs):  # type: (str, str, **Any) -> str
    log.info(cwd)
    return subprocess.check_output(cmd, cwd=cwd, shell=True, universal_newlines=True, **kwargs)  # nosec


def get_full_sha(cwd, **kwargs):  # type: (str, **Any) -> str
    return execute(cwd, "git rev-list -n 1 HEAD", **kwargs).strip()


def get_sha(cwd, **kwargs):  # type: (str, **Any) -> str
    return get_full_sha(cwd, **kwargs)[:8]


def create_commit(
    cwd,  # type: str
    message,  # type: str
    dt=None,  # type: Optional[datetime]
    **kwargs  # type: Any
):  # type: (...) -> str
    options = ""
    if dt is not None:
        options += "--date {timestamp}".format(timestamp=dt.isoformat())
    return execute(cwd, 'git commit -m "{message}" {options}'.format(message=message, options=options), **kwargs)


def create_tag(
    cwd,  # type: str
    tag,  # type: str
    message=None,  # type: Optional[str]
    commit=None,  # type: Optional[str]
    **kwargs  # type: Any
):  # type: (...) -> str
    options = ""
    if message:
        options += ' -a -m "{message}"'.format(message=message)

    if not commit:
        commit = ""

    return execute(cwd, "git tag {options} {tag} {commit}".format(options=options, tag=tag, commit=commit), **kwargs)


def checkout_branch(cwd, branch, new=True, **kwargs):  # type: (str, str, bool, **Any) -> str
    options = ""
    if new:
        options += " -b"
    return execute(cwd, "git checkout {options} {branch}".format(options=options, branch=branch), **kwargs)


def create_file(
    cwd,  # type: str
    name=None,  # type: Optional[str]
    content=None,  # type: Optional[str]
    add=True,  # type: bool
    commit=True,  # type: bool
    **kwargs  # type: Any
):  # type: (...) -> Optional[str]
    result = None

    if not name:
        name = rand_str()
    if content is None:
        content = rand_str()

    log.warning(content)
    with open(os.path.join(cwd, name), "w") as f:
        f.write(content)

    if add:
        execute(cwd, "git add {name}".format(name=name))
        log.info(execute(cwd, "git status"))
        log.info(execute(cwd, "git diff"))

        if commit:
            create_commit(cwd, "Add {name}".format(name=name))
            result = get_sha(cwd)

    return result


def create_pyproject_toml(
    cwd,  # type: str
    config=None,  # type: Optional[dict]
    commit=True,  # type: bool
    **kwargs  # type: Any
):  # type: (...) -> Optional[str]
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

    cfg = {}  # type: Dict[str, Any]
    cfg["build-system"] = {
        "requires": [
            "setuptools>=41",
            "wheel",
            "setuptools-git-versioning",
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

    return create_file(cwd, "pyproject.toml", toml.dumps(cfg), commit=commit, **kwargs)


def create_setup_py(
    cwd,  # type: str
    config=None,  # type: Optional[dict]
    option="setuptools_git_versioning",  # # type: str
    **kwargs  # type: Any
):  # type: (...) -> Optional[str]

    if config is None:
        config = {"enabled": True}

    if config == NotImplemented:
        cfg = ""
    else:
        cfg = "{option}={config},".format(option=option, config=config)

    return create_file(
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
                    {cfg}
                    setup_requires=[
                        "setuptools>=41",
                        "wheel",
                        "setuptools-git-versioning",
                    ]
                )
            finally:
                coverage.stop()
                coverage.save()
            """
        ).format(cfg=cfg),
        **kwargs,
    )


def typed_config(
    repo,  # type: str
    config_creator,  # type: Callable
    config_type,  # type: str
    template=None,  # type: Optional[str]
    template_name=None,  # type: Optional[str]
    config=None,  # type: Optional[dict]
):
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


def get_version_setup_py(cwd, **kwargs):  # type: (str, **Any) -> str
    return execute(cwd, "{python} setup.py --version".format(python=sys.executable), **kwargs).strip()


def get_version(cwd, isolated=False, **kwargs):  # type: (str, bool, **Any) -> str
    cmd = "{python} -m build -s".format(python=sys.executable)
    if not isolated:
        cmd += " --no-isolation"
    execute(cwd, cmd, **kwargs)

    with open(os.path.join(cwd, "mypkg.egg-info/PKG-INFO")) as f:
        content = f.read().splitlines()

    for line in content:
        if line.startswith("Version: "):
            return line.replace("Version: ", "").strip()

    raise RuntimeError("Cannot get package version")
