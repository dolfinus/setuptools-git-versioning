import os
import subprocess

from distutils.errors import DistutilsSetupError

try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping

DEFAULT_TEMPLATE = "{tag}"
DEFAULT_DEV_TEMPLATE = "{tag}.dev{ccount}+git.{sha}"
DEFAULT_DIRTY_TEMPLATE = "{tag}.dev{ccount}+git.{sha}.dirty"
DEFAULT_STARTING_VERSION = '0.0.1'


def _exec(cmd):
    try:
        stdout = subprocess.check_output(cmd, shell=True,
                                         universal_newlines=True)
    except subprocess.CalledProcessError as e:
        stdout = e.output
    lines = stdout.splitlines()
    return [line.rstrip() for line in lines if line.rstrip()]


def get_branches():
    branches = _exec("git branch -l --format '%(refname:short)'")
    if branches:
        return branches
    return []


def get_branch():
    branches = _exec("git rev-parse --abbrev-ref HEAD")
    if branches:
        return branches[0]
    return None


def get_tags():
    tags = _exec("git tag --sort=-version:refname --merged")
    if tags:
        return tags
    return []


def get_tag():
    tags = get_tags()
    if tags:
        return tags[0]
    return None


def get_sha(name='HEAD'):
    sha = _exec("git rev-list -n 1 {name}".format(name=name))
    if sha:
        return sha[0]
    return None


def is_dirty():
    res = _exec("git status --short")
    if res:
        return True
    return False


def count_since(name):
    res = _exec("git rev-list --count HEAD ^{name}".format(name=name))
    if res:
        return int(res[0])
    return None


def parse_config(dist, _, value):
    if isinstance(value, bool):
        if value:
            version = version_from_git()
            dist.metadata.version = version
            return
        else:
            raise DistutilsSetupError("Can't be False")

    if not isinstance(value, Mapping):
        raise DistutilsSetupError("Config in the wrong format")

    template = value.get('template', DEFAULT_TEMPLATE)
    dev_template = value.get('dev_template', DEFAULT_DEV_TEMPLATE)
    dirty_template = value.get('dirty_template', DEFAULT_DIRTY_TEMPLATE)
    starting_version = value.get('starting_version', DEFAULT_STARTING_VERSION)

    version = version_from_git(
        template=template,
        dev_template=dev_template,
        dirty_template=dirty_template,
        starting_version=starting_version,
    )
    dist.metadata.version = version


def version_from_git(template=DEFAULT_TEMPLATE,
                     dev_template=DEFAULT_DEV_TEMPLATE,
                     dirty_template=DEFAULT_DIRTY_TEMPLATE,
                     starting_version=DEFAULT_STARTING_VERSION,
                     ):

    # Check if PKG-INFO exists and return value in that if it does
    if os.path.exists('PKG-INFO'):
        with open('PKG-INFO', 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith('Version:'):
                return line[8:].strip()

    tag = get_tag()
    if tag is None:
        return starting_version

    dirty = is_dirty()
    tag_sha = get_sha(tag)
    head_sha = get_sha()
    ccount = count_since(tag)
    on_tag = head_sha == tag_sha
    branch = get_branch()

    if dirty:
        t = dirty_template
    elif not on_tag:
        t = dev_template
    else:
        t = template

    return t.format(sha=head_sha[:8], tag=tag, ccount=ccount, branch=branch)
