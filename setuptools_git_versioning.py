from __future__ import annotations

import argparse
import importlib
import inspect
import logging
import os
import re
import subprocess  # nosec
import sys
import textwrap
import warnings
from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any, Callable

from deprecated import deprecated
from packaging.version import Version
from setuptools.dist import Distribution

DEFAULT_TEMPLATE = "{tag}"
DEFAULT_DEV_TEMPLATE = "{tag}.post{ccount}+git.{sha}"
DEFAULT_DIRTY_TEMPLATE = "{tag}.post{ccount}+git.{sha}.dirty"
DEFAULT_STARTING_VERSION = "0.0.1"
DEFAULT_SORT_BY = "creatordate"
DEFAULT_TAG_FILTER = None
ENV_VARS_REGEXP = re.compile(r"\{env:(?P<name>[^:}]+):?(?P<default>[^}]+\}*)?\}", re.IGNORECASE | re.UNICODE)
TIMESTAMP_REGEXP = re.compile(r"\{timestamp:?(?P<fmt>[^:}]+)?\}", re.IGNORECASE | re.UNICODE)

# https://github.com/pypa/setuptools/blob/bc39d28bda2a1faee6680ae30e42526b9d775151/setuptools/command/dist_info.py#L108-L131
UNSUPPORTED_SYMBOL_REGEXP = re.compile(r"[^\w\d]+", re.IGNORECASE | re.UNICODE)

LOG_FORMAT = "[%(asctime)s] %(levelname)+8s: %(message)s"
# setuptools v60.2.0 changed default logging level to DEBUG: https://github.com/pypa/setuptools/pull/2974
# to avoid printing information messages to the same output as version number,
# use a custom levels below built-in DEBUG level (10)
INFO = 9
DEBUG = 8
logging.addLevelName(INFO, "INF0")
logging.addLevelName(DEBUG, "DE8UG")
VERBOSITY_LEVELS = {
    0: logging.WARNING,
    1: INFO,
    2: DEBUG,
}

DEFAULT_CONFIG = {
    "template": DEFAULT_TEMPLATE,
    "dev_template": DEFAULT_DEV_TEMPLATE,
    "dirty_template": DEFAULT_DIRTY_TEMPLATE,
    "starting_version": DEFAULT_STARTING_VERSION,
    "version_callback": None,
    "version_file": None,
    "count_commits_from_version_file": False,
    "tag_formatter": None,
    "branch_formatter": None,
    "sort_by": DEFAULT_SORT_BY,
    "tag_filter": DEFAULT_TAG_FILTER,
}

log = logging.getLogger(__name__)


def _exec(cmd: str, root: str | os.PathLike | None = None) -> list[str]:
    log.log(DEBUG, "Executing %r at '%s'", cmd, root or os.getcwd())
    try:
        stdout = subprocess.check_output(cmd, shell=True, text=True, cwd=root)  # nosec
    except subprocess.CalledProcessError as e:
        stdout = e.output
    lines = stdout.splitlines()
    return [line.rstrip() for line in lines if line.rstrip()]


def get_branches(root: str | os.PathLike | None = None) -> list[str]:
    """Return list of branch names in the git repository"""
    branches = _exec("git branch -l --format '%(refname:short)'", root=root)
    if branches:
        return branches
    return []


def get_branch(root: str | os.PathLike | None = None) -> str | None:
    """Return branch name pointing to HEAD, or None"""
    branches = _exec("git rev-parse --abbrev-ref HEAD", root=root)
    if branches:
        return branches[0]
    return None


def get_all_tags(sort_by: str = DEFAULT_SORT_BY, root: str | os.PathLike | None = None) -> list[str]:
    """Return list of tags in the git repository"""
    tags = _exec(f"git tag --sort=-{sort_by}", root=root)
    if tags:
        return tags
    return []


@deprecated(version="1.8.0", reason="will be dropped in v2.0.0. Please use 'get_tags' instead")
def get_branch_tags(*args, **kwargs) -> list[str]:
    return get_tags(*args, **kwargs)


def get_tags(
    sort_by: str = DEFAULT_SORT_BY,
    filter_callback: Callable[[str], str | None] | None = None,
    root: str | os.PathLike | None = None,
) -> list[str]:
    """Return list of tags merged into HEAD history tree"""
    tags = _exec(f"git tag --sort=-{sort_by} --merged", root=root)
    if filter_callback:
        # pull the tags that don't start with tag_prefix out of the list
        mytags = list(filter(filter_callback, tags))
        return mytags
    if tags:
        return tags
    return []


def get_tag(*args, **kwargs) -> str | None:
    """Return latest tag merged into HEAD history tree"""
    tags = get_tags(*args, **kwargs)
    if tags:
        return tags[0]
    return None


def get_sha(name: str = "HEAD", root: str | os.PathLike | None = None) -> str | None:
    """Get commit SHA-1 hash"""
    sha = _exec(f'git rev-list -n 1 "{name}"', root=root)
    if sha:
        return sha[0]
    return None


def get_latest_file_commit(path: str | os.PathLike, root: str | os.PathLike | None = None) -> str | None:
    """Get SHA-1 hash of latest commit of the file in the repository"""
    sha = _exec(f'git log -n 1 --pretty=format:%H -- "{path}"', root=root)
    if sha:
        return sha[0]
    return None


def is_dirty(root: str | os.PathLike | None = None) -> bool:
    """Check index status, and return True if there are some uncommitted changes"""
    res = _exec("git status --short", root=root)
    if res:
        return True
    return False


def count_since(name: str, root: str | os.PathLike | None = None) -> int | None:
    """Get number of commits between HEAD and the commit, or None if they are not related"""
    res = _exec(f'git rev-list --count HEAD "^{name}"', root=root)
    if res:
        return int(res[0])
    return None


def _set_default_options(config: dict):
    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)


def _read_toml(name_or_path: str | os.PathLike = "pyproject.toml", root: str | os.PathLike | None = None) -> dict:
    file_path = Path(root or os.getcwd()).joinpath(name_or_path)
    if not file_path.exists():
        log.log(INFO, "'%s' does not exist", file_path)
        return {}

    if not file_path.is_file():
        raise OSError(f"'{file_path}' is not a file")

    log.log(INFO, "Trying 'pyproject.toml' ...")
    try:
        # for Python 3.11
        import tomllib

        with file_path.open("rb") as file:
            parsed_file = tomllib.load(file)
    except (ImportError, NameError):
        import toml  # type: ignore[no-redef]

        parsed_file = toml.load(file_path)

    result = parsed_file.get("tool", {}).get("setuptools-git-versioning", None)
    if result:
        log.log(DEBUG, "'tool.setuptools-git-versioning' section content:\n%s", pformat(result))
    return result


def _infer_setup_py(name_or_path: str = "setup.py", root: str | os.PathLike | None = None) -> str | None:
    root_path = Path(root or os.getcwd())
    file_path = root_path.joinpath(name_or_path)
    if not file_path.exists():
        log.log(INFO, "'%s' does not exist", file_path)
        return None

    from distutils.core import run_setup

    # distutils does not change current directory, causing version of 'setuptools_git_versioning'
    # is being get instead of target package.
    # also some setup.py files can contain imports of other files from the package,
    # and if they will be missing from sys.path, import will fail.
    # emulating `python setup.py` call by modifying current dir and sys.path, but restore everything back after import
    original_cwd = os.getcwd()
    original_sys_path = sys.path.copy()
    original_sys_modules = sys.modules.copy()
    try:
        _add_to_sys_path(root_path)
        os.chdir(root_path)
        dist = run_setup(os.fspath(file_path), stop_after="init")
        return _infer_version(dist, root=root)
    finally:
        sys.path[:] = original_sys_path
        sys.modules = original_sys_modules
        os.chdir(original_cwd)


# TODO: remove along with version_config
def _parse_config(dist: Distribution, attr: Any, value: Any) -> None:
    from distutils.errors import DistutilsOptionError

    if attr == "version_config" and value is not None:
        warnings.warn(
            "'version_config' option is deprecated "
            "since setuptools-git-versioning v1.8.0 "
            "and will be dropped in v2.0.0\n"
            "Please rename it to 'setuptools_git_versioning'",
            category=UserWarning,
        )

        if getattr(dist, "setuptools_git_versioning", None) is not None:
            raise DistutilsOptionError(
                "You can set either 'version_config' or 'setuptools_git_versioning' "
                "but not both of them at the same time"
            )


def _infer_version(dist: Distribution, root: str | os.PathLike | None = None) -> str | None:
    log.log(INFO, "Trying 'setup.py' ...")

    from distutils.errors import DistutilsOptionError, DistutilsSetupError

    config = getattr(dist, "setuptools_git_versioning", None) or getattr(dist, "version_config", None)

    if isinstance(config, bool):
        warnings.warn(
            "Passing boolean value to 'version_config'/'setuptools_git_versioning' option is deprecated "
            "since setuptools-git-versioning 1.8.0 "
            "and will be dropped in v2.0.0\n"
            "Please change value to '{'enabled': False/True}'",
            category=UserWarning,
        )
        config = {"enabled": config}

    toml_config = _read_toml(root=root)

    if config is None:
        config = toml_config
    elif toml_config:
        raise DistutilsSetupError(
            "Both 'setup.py' and 'pyproject.toml' have 'setuptools_git_versioning' config section. "
            "Please remove one of them",
        )

    if config is None:
        # Nothing to do here
        return None

    if not isinstance(config, dict):
        raise DistutilsOptionError(f"Wrong config format. Expected dict, got: {config}")

    if not config or not config.pop("enabled", True):
        # Nothing to do here
        return None

    _set_default_options(config)

    version = version_from_git(dist.metadata.name, **config, root=root)
    dist.metadata.version = version
    return version


def _read_version_from_file(name_or_path: str | os.PathLike, root: str | os.PathLike | None = None) -> str:
    return Path(root or os.getcwd()).joinpath(name_or_path).read_text().strip()


def _substitute_env_variables(template: str) -> str:
    log.log(DEBUG, "Substitute environment variables in template %r", template)
    for var, default in ENV_VARS_REGEXP.findall(template):
        log.log(DEBUG, "Variable: %r", var)

        if default.upper() == "IGNORE":
            default = ""
        elif not default:
            default = "UNKNOWN"
        log.log(DEBUG, "Default: %r", default)

        value = os.environ.get(var, default)
        log.log(DEBUG, "Value: %r", value)

        template, _ = ENV_VARS_REGEXP.subn(value, template, count=1)

    log.log(DEBUG, "Result: %r", template)
    return template


def _substitute_timestamp(template: str) -> str:
    log.log(DEBUG, "Substitute timestamps in template %r", template)

    now = datetime.now()
    for fmt in TIMESTAMP_REGEXP.findall(template):
        format_string = fmt or "%s"
        log.log(DEBUG, "Format: %r", format_string)

        result = now.strftime(format_string)
        log.log(DEBUG, "Value: %r", result)

        template, _ = TIMESTAMP_REGEXP.subn(result, template, count=1)

    log.log(DEBUG, "Result: %r", template)
    return template


def _resolve_substitutions(template: str, *args, **kwargs) -> str:
    log.log(DEBUG, "Template: %r", template)
    log.log(DEBUG, "Args:%s", pformat(args))

    while True:
        if "{env" in template:
            new_template = _substitute_env_variables(template)
            if new_template == template:
                break
            else:
                template = new_template
        else:
            break

    if "{timestamp" in template:
        template = _substitute_timestamp(template)

    return template.format(*args, **kwargs)


def _add_to_sys_path(root: str | os.PathLike | None) -> None:
    root_path = os.fspath(Path(root or os.getcwd()))
    if root_path not in sys.path:
        log.log(DEBUG, "Adding '%s' folder to sys.path", root_path)
        sys.path.insert(0, root_path)


def _import_reference(
    ref: str,
    package_name: str | None = None,
    root: str | os.PathLike | None = None,
) -> Any:
    if ":" not in ref:
        raise NameError(f"Wrong reference name: {ref}")

    _add_to_sys_path(root)

    module_name, attr = ref.split(":")
    log.log(DEBUG, "Executing 'from %s.%s import %s'", package_name or "", module_name, attr)
    module = importlib.import_module(module_name, package_name)

    return getattr(module, attr)


def _load_callable(
    inp: str,
    package_name: str | None = None,
    root: str | os.PathLike | None = None,
) -> Callable:
    ref = _import_reference(inp, package_name, root=root)
    if not callable(ref):
        raise ValueError(f"{ref} of type {type(ref)} is not callable")

    return ref


def _load_tag_formatter(
    tag_formatter: str | Callable[[str], str],
    package_name: str | None = None,
    root: str | os.PathLike | None = None,
) -> Callable:
    log.log(INFO, "Parsing tag_formatter %r of type %r", tag_formatter, type(tag_formatter).__name__)

    if callable(tag_formatter):
        log.log(DEBUG, "Value is callable with signature %s", inspect.Signature.from_callable(tag_formatter))
        return tag_formatter

    try:
        return _load_callable(tag_formatter, package_name, root=root)
    except (ImportError, NameError) as e:
        log.warning("tag_formatter is not a valid function reference: %s", e)

    try:
        pattern = re.compile(tag_formatter)

        def formatter(tag):
            match = pattern.match(tag)
            if match:
                return match.group("tag")

            raise ValueError(f"Tag name {tag} does not match regexp '{tag_formatter}'")

        return formatter
    except re.error as e:
        log.error("tag_formatter is not valid regexp: %s", e)
        raise ValueError("Cannot parse tag_formatter") from e


def _load_branch_formatter(
    branch_formatter: str | Callable[[str], str],
    package_name: str | None = None,
    root: str | os.PathLike | None = None,
) -> Callable:
    log.log(INFO, "Parsing branch_formatter %r of type %r", branch_formatter, type(branch_formatter).__name__)

    if callable(branch_formatter):
        log.log(DEBUG, "Value is callable with signature %s", inspect.Signature.from_callable(branch_formatter))
        return branch_formatter

    try:
        return _load_callable(branch_formatter, package_name, root=root)
    except (ImportError, NameError) as e:
        log.warning("branch_formatter is not a valid function reference: %s", e)

    try:
        pattern = re.compile(branch_formatter)

        def formatter(branch):
            match = pattern.match(branch)
            if match:
                return match.group("branch")

            raise ValueError(f"Branch name {branch} does not match regexp '{branch_formatter}'")

        return formatter
    except re.error as e:
        log.error("branch_formatter is not valid regexp: %s", e)
        raise ValueError("Cannot parse branch_formatter") from e


def _load_tag_filter(
    tag_filter: str | Callable[[str], str | None],
    package_name: str | None = None,
    root: str | os.PathLike | None = None,
) -> Callable[[str], str | None]:
    log.log(INFO, "Parsing tag_filter %r of type %r", tag_filter, type(tag_filter).__name__)

    if callable(tag_filter):
        log.log(DEBUG, "Value is callable with signature %s", inspect.Signature.from_callable(tag_filter))
        return tag_filter

    try:
        return _load_callable(tag_filter, package_name, root=root)
    except (ImportError, NameError) as e:
        log.warning("tag_filter is not a valid function reference: %s", e)

    try:
        pattern = re.compile(tag_filter)

        def formatter(tag: str) -> str | None:
            match = pattern.match(tag)
            if match:
                log.error("Matched %s", tag)
                return tag
            else:
                return None

        return formatter
    except re.error as e:
        log.error("tag_filter is not valid regexp: %s", e)
        raise ValueError("Cannot parse tag_filter") from e


# TODO: return Version object instead of str
def _get_version_from_callback(
    version_callback: str | Callable[[], str],
    package_name: str | None = None,
    root: str | os.PathLike | None = None,
) -> str:
    log.log(INFO, "Parsing version_callback %r of type %r", version_callback, type(version_callback).__name__)

    if callable(version_callback):
        log.log(DEBUG, "Value is callable with signature %s", inspect.Signature.from_callable(version_callback))
        result = version_callback()
    else:

        log.log(INFO, "Is not callable, trying to import ...")
        result = version_callback

        try:
            callback = _load_callable(version_callback, package_name, root=root)
            result = callback()
        except ValueError as e:
            log.log(INFO, "Is not a callable")
            log.log(DEBUG, str(e))
            log.log(INFO, "Assuming it is a string attribute")
            result = _import_reference(version_callback, package_name, root=root)
        except (ImportError, NameError) as e:
            log.warning("version_callback is not a valid reference: %s", e)

    return _sanitize_version(result)


def _sanitize_version(version: str) -> str:
    log.log(INFO, "Before sanitization %r", version)

    public, sep, local = version.partition("+")

    # replace "feature/ABC-123" with "feature.ABC.123"
    sanitized_public = UNSUPPORTED_SYMBOL_REGEXP.sub(".", public)
    sanitized_local = UNSUPPORTED_SYMBOL_REGEXP.sub(".", local)

    sanitized_version = sanitized_public + sep + sanitized_local
    sanitized_version = sanitized_version.rstrip(".")

    # replace "feature.ABC.123" with "feature.abc.123"
    # drop leading "v" symbol
    # other replacements according to PEP-440, like "-dev" -> ".dev"
    result = str(Version(sanitized_version))
    log.log(INFO, "Result %r", result)
    return result


# TODO: return Version object instead of str
def version_from_git(
    package_name: str | None = None,
    template: str = DEFAULT_TEMPLATE,
    dev_template: str = DEFAULT_DEV_TEMPLATE,
    dirty_template: str = DEFAULT_DIRTY_TEMPLATE,
    starting_version: str = DEFAULT_STARTING_VERSION,
    version_callback: str | Callable[[], str] | None = None,
    version_file: str | os.PathLike | None = None,
    count_commits_from_version_file: bool = False,
    tag_formatter: Callable[[str], str] | str | None = None,
    branch_formatter: Callable[[str], str] | None = None,
    tag_filter: Callable[[str], str | None] | str | None = None,
    sort_by: str = DEFAULT_SORT_BY,
    root: str | os.PathLike | None = None,
) -> str:
    # Check if PKG-INFO file exists and Version is present in it
    pkg_info = Path(root or os.getcwd()).joinpath("PKG-INFO")
    if pkg_info.exists():
        log.log(INFO, "File '%s' is found, reading its content", pkg_info)
        lines = pkg_info.read_text().splitlines()
        for line in lines:
            if line.startswith("Version:"):
                result = line[8:].strip()
                log.log(INFO, "Return %r", result)
                return _sanitize_version(result)

    if version_callback is not None:
        if version_file is not None:
            raise ValueError(
                "Either 'version_file' or 'version_callback' can be passed, but not both at the same time",
            )
        return _get_version_from_callback(version_callback, package_name, root=root)

    filter_callback = None
    if tag_filter:
        filter_callback = _load_tag_filter(tag_filter=tag_filter, package_name=package_name, root=root)

    from_file = False
    log.log(INFO, "Getting latest tag")
    log.log(DEBUG, "Sorting tags by %r", sort_by)
    tag = get_tag(sort_by=sort_by, root=root, filter_callback=filter_callback)

    if tag is None:
        log.log(INFO, "No tag, checking for 'version_file'")
        if version_file is None:
            log.log(INFO, "No 'version_file' set, return starting_version %r", starting_version)
            return _sanitize_version(starting_version)

        if not Path(version_file).exists():
            log.log(
                INFO,
                "version_file '%s' does not exist, return starting_version %r",
                version_file,
                starting_version,
            )
            return _sanitize_version(starting_version)

        log.log(INFO, "version_file '%s' does exist, reading its content", version_file)
        from_file = True
        tag = _read_version_from_file(version_file, root=root)

        if not tag:
            log.log(INFO, "File is empty, return starting_version %r", version_file, starting_version)
            return _sanitize_version(starting_version)

        log.log(DEBUG, "File content: %r", tag)
        if not count_commits_from_version_file:
            return _sanitize_version(tag)

        tag_sha = get_latest_file_commit(version_file, root=root)
        log.log(DEBUG, "File SHA-256: %r", tag_sha)
    else:
        log.log(INFO, "Latest tag: %r", tag)
        tag_sha = get_sha(tag, root=root)
        log.log(INFO, "Tag SHA-256: %r", tag_sha)

        if tag_formatter is not None:
            tag_fmt = _load_tag_formatter(tag_formatter, package_name, root=root)
            tag = tag_fmt(tag)
            log.log(DEBUG, "Tag after formatting: %r", tag)

    dirty = is_dirty(root=root)
    log.log(INFO, "Is dirty: %r", dirty)

    head_sha = get_sha(root=root)
    log.log(INFO, "HEAD SHA-256: %r", head_sha)

    full_sha = head_sha if head_sha is not None else ""
    ccount = count_since(tag_sha, root=root) if tag_sha is not None else None
    log.log(INFO, "Commits count between HEAD and latest tag: %r", ccount)

    on_tag = head_sha is not None and head_sha == tag_sha and not from_file
    log.log(INFO, "HEAD is tagged: %r", on_tag)

    branch = get_branch(root=root)
    log.log(INFO, "Current branch: %r", branch)

    if branch_formatter is not None and branch is not None:
        branch_fmt = _load_branch_formatter(branch_formatter, package_name, root=root)
        branch = branch_fmt(branch)
        log.log(INFO, "Branch after formatting: %r", branch)

    if dirty:
        log.log(INFO, "Using template from 'dirty_template' option")
        t = dirty_template
    elif not on_tag and ccount is not None:
        log.log(INFO, "Using template from 'dev_template' option")
        t = dev_template
    else:
        log.log(INFO, "Using template from 'template' option")
        t = template

    version = _resolve_substitutions(t, sha=full_sha[:8], tag=tag, ccount=ccount, branch=branch, full_sha=full_sha)
    log.log(INFO, "Version number after resolving substitutions: %r", version)
    return _sanitize_version(version)


def get_version(config: dict | None = None, root: str | os.PathLike | None = None) -> Version:
    if not config:
        log.log(INFO, "No explicit config passed")
        log.log(INFO, "Searching for config files in '%s' folder", root or os.getcwd())
        result = _infer_setup_py(root=root)
        if result is not None:
            return Version(result)

        config = _read_toml(root=root)

    if not config or not config.pop("enabled", True):
        raise RuntimeError(
            textwrap.dedent(
                f"""
                'setuptools-git-versioning' command can be used only
                with 'pyproject.toml' or 'setup.py' file present in folder '{root or os.getcwd()}',
                containing the 'enabled: True' setting
                (see https://setuptools-git-versioning.readthedocs.io/en/stable/install.html)
                """,
            ),
        )

    if not isinstance(config, dict):
        raise RuntimeError(f"Wrong config format. Expected dict, got: {config}")

    _set_default_options(config)
    result = version_from_git(**config, root=root)
    return Version(result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setuptools-git-versioning",
        description="Get version based on git information and 'setup.py' or 'pyproject.toml' config",
    )
    parser.add_argument(
        "root",
        type=str,
        default=None,
        nargs="?",
        help="Path to folder containing 'setup.py' or 'pyproject.toml' file. Default: current dir",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity level. Can be used multiple times: -v for INFO messages, -vv for DEBUG",
    )
    return parser


def __main__():
    parser = _parser()
    namespace = parser.parse_args()
    log_level = VERBOSITY_LEVELS.get(namespace.verbose, logging.DEBUG)
    logging.basicConfig(level=log_level, format=LOG_FORMAT, stream=sys.stderr)
    print(str(get_version(root=namespace.root)))


if __name__ == "__main__":
    __main__()
