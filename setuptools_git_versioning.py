import os
import re
import subprocess

from setuptools.dist import Distribution
from distutils.errors import DistutilsSetupError
from typing import List, Optional, Any, Callable
from six.moves import collections_abc

DEFAULT_TEMPLATE = "{tag}"  # type: str
DEFAULT_DEV_TEMPLATE = "{tag}.post{ccount}+git.{sha}"  # type: str
DEFAULT_DIRTY_TEMPLATE = "{tag}.post{ccount}+git.{sha}.dirty"  # type: str
DEFAULT_STARTING_VERSION = '0.0.1'


def _exec(cmd):  # type: (str) -> List[str]
    try:
        stdout = subprocess.check_output(cmd, shell=True,
                                         universal_newlines=True)
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


def get_all_tags():  # type: () -> List[str]
    tags = _exec("git tag --sort=-version:refname")
    if tags:
        return tags
    return []


def get_branch_tags():  # type: () -> List[str]
    tags = _exec("git tag --sort=-version:refname --merged")
    if tags:
        return tags
    return []


def get_tags():  # type: () -> List[str]
    return get_branch_tags


def get_tag():  # type: () -> Optional[str]
    tags = get_branch_tags()
    if tags:
        return tags[0]
    return None


def get_sha(name='HEAD'):  # type: (str) -> Optional[str]
    sha = _exec("git rev-list -n 1 \"{name}\"".format(name=name))
    if sha:
        return sha[0]
    return None


def get_latest_file_commit(path):  # type: (str) -> Optional[str]
    sha = _exec("git log -n 1 --pretty=format:%H -- \"{path}\"".format(path=path))
    if sha:
        return sha[0]
    return None


def is_dirty():  # type: () -> bool
    res = _exec("git status --short")
    if res:
        return True
    return False


def count_since(name):  # type: (str) -> Optional[int]
    res = _exec("git rev-list --count HEAD \"^{name}\"".format(name=name))
    if res:
        return int(res[0])
    return None


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

    template = value.get('template', DEFAULT_TEMPLATE)
    dev_template = value.get('dev_template', DEFAULT_DEV_TEMPLATE)
    dirty_template = value.get('dirty_template', DEFAULT_DIRTY_TEMPLATE)
    starting_version = value.get('starting_version', DEFAULT_STARTING_VERSION)
    version_callback = value.get('version_callback', None)
    version_file = value.get('version_file', None)
    count_commits_from_version_file = value.get('count_commits_from_version_file', False)
    branch_formatter = value.get('branch_formatter', None)

    version = version_from_git(
        template=template,
        dev_template=dev_template,
        dirty_template=dirty_template,
        starting_version=starting_version,
        version_callback=version_callback,
        version_file=version_file,
        count_commits_from_version_file=count_commits_from_version_file,
        branch_formatter=branch_formatter
    )
    dist.metadata.version = version


def read_version_from_file(path):
    with open(path, 'r') as file:
        return file.read().strip()


def version_from_git(template=DEFAULT_TEMPLATE,
                     dev_template=DEFAULT_DEV_TEMPLATE,
                     dirty_template=DEFAULT_DIRTY_TEMPLATE,
                     starting_version=DEFAULT_STARTING_VERSION,
                     version_callback=None,
                     version_file=None,
                     count_commits_from_version_file=False,
                     branch_formatter=None,
                     ):
    # type: (str, str, str, str, Optional[Any, Callable], Optional[str], bool, Optional[Callable[[str], str]]) -> str

    # Check if PKG-INFO exists and return value in that if it does
    if os.path.exists('PKG-INFO'):
        with open('PKG-INFO', 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith('Version:'):
                return line[8:].strip()

    from_file = False
    tag = get_tag()
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
                return tag

            tag_sha = get_latest_file_commit(version_file)
    else:
        tag_sha = get_sha(tag)

    dirty = is_dirty()
    head_sha = get_sha()
    full_sha = head_sha if head_sha is not None else ''
    ccount = count_since(tag_sha)
    on_tag = head_sha is not None and head_sha == tag_sha and not from_file
    branch = get_branch() if branch_formatter is None else branch_formatter(get_branch())

    if dirty:
        t = dirty_template
    elif not on_tag and ccount is not None:
        t = dev_template
    else:
        t = template

    version = t.format(sha=full_sha[:8], tag=tag, ccount=ccount, branch=branch, full_sha=full_sha)

    # Ensure local version label only contains permitted characters
    public, sep, local = version.partition('+')
    local_sanitized = re.sub(r'[^a-zA-Z0-9.]', '.', local)
    return public + sep + local_sanitized
