import os
import re
import subprocess
from datetime import datetime
from distutils.errors import DistutilsSetupError
from typing import Any, Callable, List, Optional, Union

import toml
from setuptools.dist import Distribution
from six.moves import collections_abc

DEFAULT_TEMPLATE = "{tag}"  # type: str
DEFAULT_DEV_TEMPLATE = "{tag}.post{ccount}+git.{sha}"  # type: str
DEFAULT_DIRTY_TEMPLATE = "{tag}.post{ccount}+git.{sha}.dirty"  # type: str
DEFAULT_STARTING_VERSION = "0.0.1"
ENV_VARS_REGEXP = re.compile(r"\{env:([^:}]+):?([^}]+}?)?\}", re.IGNORECASE | re.UNICODE)  # type: re.Pattern
TIMESTAMP_REGEXP = re.compile(r"\{timestamp:?([^:}]+)?\}", re.IGNORECASE | re.UNICODE)  # type: re.Pattern

DEFAULT_CONFIG = {
    "template": DEFAULT_TEMPLATE,
    "dev_template": DEFAULT_DEV_TEMPLATE,
    "dirty_template": DEFAULT_DIRTY_TEMPLATE,
    "starting_version": DEFAULT_STARTING_VERSION,
    "version_callback": None,
    "version_file": None,
    "count_commits_from_version_file": False,
    "branch_formatter": None,
    "sort_by": None,
}


def _exec(cmd):  # type: (str) -> List[str]
    try:
        stdout = subprocess.check_output(cmd, shell=True, universal_newlines=True)  # nosec
    except subprocess.CalledProcessError as e:
        stdout = e.output
    lines = stdout.splitlines()
    return [line.rstrip() for line in lines if line.rstrip()]


def get_branches():  # type: () -> List[str]
    branches = _exec("git branch -l --format '%(refname:short)'")
    if branches:
        return branches
    return []


def get_branch():  # type: () -> Optional[str]
    branches = _exec("git rev-parse --abbrev-ref HEAD")
    if branches:
        return branches[0]
    return None


def get_all_tags(sort_by="creatordate"):  # type: (str) -> List[str]
    tags = _exec("git tag --sort=-{}".format(sort_by))
    if tags:
        return tags
    return []


def get_branch_tags(sort_by="creatordate"):  # type: (str) -> List[str]
    tags = _exec("git tag --sort=-{} --merged".format(sort_by))
    if tags:
        return tags
    return []


def get_tags(*args, **kwargs):  # type: (*str, **str) -> List[str]
    return get_branch_tags(*args, **kwargs)


def get_tag(*args, **kwargs):  # type: (*str, **str) -> Optional[str]
    tags = get_branch_tags(*args, **kwargs)
    if tags:
        return tags[0]
    return None


def get_sha(name="HEAD"):  # type: (str) -> Optional[str]
    sha = _exec('git rev-list -n 1 "{}"'.format(name))
    if sha:
        return sha[0]
    return None


def get_latest_file_commit(path):  # type: (str) -> Optional[str]
    sha = _exec('git log -n 1 --pretty=format:%H -- "{}"'.format(path))
    if sha:
        return sha[0]
    return None


def is_dirty():  # type: () -> bool
    res = _exec("git status --short")
    if res:
        return True
    return False


def count_since(name):  # type: (str) -> Optional[int]
    res = _exec('git rev-list --count HEAD "^{}"'.format(name))
    if res:
        return int(res[0])
    return None


def load_config_from_dict(dictionary):  # type: (Union[dict, collections_abc.Mapping]) -> dict
    config = {}
    for key, value in DEFAULT_CONFIG.items():
        config[key] = dictionary.get(key, value)
    return config


def load_config_from_toml(file_name):  # type: (str) -> dict
    with open(file_name, encoding="UTF-8", mode="r") as f:
        data = f.read()
    parsed_file = toml.loads(data)

    filtered_file = parsed_file.get("tool", {}).get("setuptools_git_versioning", {})

    config = load_config_from_dict(filtered_file)

    return config


def infer_version(dist):  # type: (Distribution) -> None
    pyproject = "pyproject.toml"
    if not os.path.isfile(pyproject):
        return

    config = load_config_from_toml(pyproject)

    version = version_from_git(**config)

    dist.metadata.version = version


def parse_config(dist, _, value):  # type: (Distribution, Any, Any) -> None
    if isinstance(value, bool):
        if value:
            version = version_from_git()
            dist.metadata.version = version
            return
        else:
            raise DistutilsSetupError("Can't be False")

    if not isinstance(value, collections_abc.Mapping):
        raise DistutilsSetupError("Config in the wrong format")

    config = load_config_from_dict(value)

    version = version_from_git(**config)

    dist.metadata.version = version

    infer_version(dist)


def read_version_from_file(path):  # type: (Union[str, os.PathLike]) -> str
    with open(path) as file:
        return file.read().strip()


def subst_env_variables(template):  # type: (str) -> str
    if "{env" in template:
        for var, default in ENV_VARS_REGEXP.findall(template):
            if default.upper() == "IGNORE":
                default = ""
            elif not default:
                default = "UNKNOWN"

            value = os.environ.get(var, default)
            template, _ = ENV_VARS_REGEXP.subn(value, template, count=1)

    return template


def subst_timestamp(template):  # type: (str) -> str
    if "{timestamp" in template:
        now = datetime.now()
        for fmt in TIMESTAMP_REGEXP.findall(template):
            result = now.strftime(fmt or "%s")
            template, _ = TIMESTAMP_REGEXP.subn(result, template, count=1)

    return template


def version_from_git(
    template=DEFAULT_TEMPLATE,  # type: str
    dev_template=DEFAULT_DEV_TEMPLATE,  # type: str
    dirty_template=DEFAULT_DIRTY_TEMPLATE,  # type: str
    starting_version=DEFAULT_STARTING_VERSION,  # type: str
    version_callback=None,  # type: Union[Any, Callable, None]
    version_file=None,  # type: Optional[str]
    count_commits_from_version_file=False,  # type: bool
    branch_formatter=None,  # type: Optional[Callable[[str], str]]
    sort_by=None,  # type: Optional[str]
):
    # type: (...) -> str

    # Check if PKG-INFO exists and return value in that if it does
    if os.path.exists("PKG-INFO"):
        with open("PKG-INFO") as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith("Version:"):
                return line[8:].strip()

    from_file = False
    tag = get_tag(sort_by) if sort_by else get_tag()
    if tag is None:
        if version_callback is not None:
            if callable(version_callback):
                return version_callback()
            else:
                return version_callback

        if version_file is None or not os.path.exists(version_file):
            return starting_version
        else:
            from_file = True
            tag = read_version_from_file(version_file)

            if not count_commits_from_version_file:
                return tag.lstrip("v")  # for tag "v1.0.0" drop leading "v" symbol

            tag_sha = get_latest_file_commit(version_file)
    else:
        tag_sha = get_sha(tag)

    dirty = is_dirty()
    head_sha = get_sha()
    full_sha = head_sha if head_sha is not None else ""
    ccount = count_since(tag_sha) if tag_sha is not None else None
    on_tag = head_sha is not None and head_sha == tag_sha and not from_file

    branch = get_branch()
    if branch_formatter is not None and branch is not None:
        branch = branch_formatter(branch)

    if dirty:
        t = dirty_template
    elif not on_tag and ccount is not None:
        t = dev_template
    else:
        t = template

    t = subst_env_variables(t)
    t = subst_timestamp(t)

    version = t.format(sha=full_sha[:8], tag=tag, ccount=ccount, branch=branch, full_sha=full_sha)

    # Ensure local version label only contains permitted characters
    public, sep, local = version.partition("+")
    local_sanitized = re.sub(r"[^a-zA-Z0-9.]", ".", local)
    public_sanitized = public.lstrip("v")  # for version "v1.0.0" drop leading "v" symbol
    return public_sanitized + sep + local_sanitized
