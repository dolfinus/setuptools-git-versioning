from __future__ import annotations

import inspect
import logging
import os  # noqa: TC003
import re
from pathlib import Path
from typing import Callable

# avoid importing 'packaging' because setuptools-git-versioning can be installed using sdist
# where 'packaging' is not installed yet
from packaging.version import Version

from setuptools_git_versioning.archival import version_from_archival
from setuptools_git_versioning.defaults import (
    DEFAULT_DEV_TEMPLATE,
    DEFAULT_DIRTY_TEMPLATE,
    DEFAULT_SORT_BY,
    DEFAULT_STARTING_VERSION,
    DEFAULT_TEMPLATE,
)
from setuptools_git_versioning.factories import (
    create_branch_formatter,
    create_tag_filter,
    create_tag_formatter,
    import_reference,
    load_callable,
)
from setuptools_git_versioning.git import count_since, get_branch, get_latest_file_commit, get_sha, get_tag, is_dirty
from setuptools_git_versioning.log import DEBUG, INFO
from setuptools_git_versioning.subst import resolve_substitutions

# https://github.com/pypa/setuptools/blob/bc39d28bda2a1faee6680ae30e42526b9d775151/setuptools/command/dist_info.py#L108-L131
UNSUPPORTED_SYMBOL_REGEXP = re.compile(r"[^\w\d!]+", re.IGNORECASE | re.UNICODE)

log = logging.getLogger(__name__)


def get_version_from_callback(
    version_callback: str | Callable[[], str],
    package_name: str | None = None,
    root: str | os.PathLike | None = None,
) -> Version:
    log.log(INFO, "Parsing version_callback %r of type %r", version_callback, type(version_callback).__name__)

    if callable(version_callback):
        log.log(DEBUG, "Value is callable with signature %s", inspect.Signature.from_callable(version_callback))
        result = version_callback()
    else:
        log.log(INFO, "Is not callable, trying to import ...")
        result = version_callback

        try:
            callback = load_callable(version_callback, package_name, root=root)
            result = callback()
        except TypeError as e:
            log.log(INFO, "Is not a callable")
            log.log(DEBUG, str(e))
            log.log(INFO, "Assuming it is a string attribute")
            result = import_reference(version_callback, package_name, root=root)
        except (ImportError, NameError) as e:
            log.warning("version_callback is not a valid reference: %s", e)

    return sanitize_version(result)


def sanitize_version(version: str) -> Version:
    from packaging.version import Version

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
    result = Version(sanitized_version)
    log.log(INFO, "Result %s", result)
    return result


def version_from_git(  # noqa: PLR0915, PLR0912, PLR0913, C901
    package_name: str | None = None,
    *,
    template: str = DEFAULT_TEMPLATE,
    dev_template: str = DEFAULT_DEV_TEMPLATE,
    dirty_template: str = DEFAULT_DIRTY_TEMPLATE,
    starting_version: str = DEFAULT_STARTING_VERSION,
    version_callback: str | Callable[[], str] | None = None,
    version_file: str | os.PathLike | None = None,
    count_commits_from_version_file: bool = False,
    prefer_tag: bool = False,
    tag_formatter: Callable[[str], str] | str | None = None,
    branch_formatter: Callable[[str], str] | str | None = None,
    tag_filter: Callable[[str], str | None] | str | None = None,
    sort_by: str = DEFAULT_SORT_BY,
    root: str | os.PathLike | None = None,
) -> Version:
    # Check if PKG-INFO file exists and Version is present in it
    project_root = Path(root) if root else Path.cwd()
    pkg_info = project_root.joinpath("PKG-INFO")
    if pkg_info.exists():
        log.log(INFO, "File '%s' is found, reading its content", pkg_info)
        lines = pkg_info.read_text().splitlines()
        for line in lines:
            if line.startswith("Version:"):
                version_str = line[8:].strip()
                log.log(INFO, "Return %s", version_str)
                # running on sdist package, do not sanitize
                return Version(version_str)

    archival_version = version_from_archival(
        project_root,
        package_name=package_name,
        template=template,
        dev_template=dev_template,
        dirty_template=dirty_template,
        tag_formatter=tag_formatter,
        branch_formatter=branch_formatter,
    )
    if archival_version is not None:
        log.log(INFO, "Resolved version from '.git_archival.txt': %s", archival_version)
        return archival_version

    if version_callback is not None:
        if version_file is not None:
            msg = "Either 'version_file' or 'version_callback' can be passed, but not both at the same time"
            raise ValueError(msg)
        return get_version_from_callback(version_callback, package_name, root=root)

    head_sha = get_sha(root=root)
    log.log(INFO, "HEAD SHA-256: %r", head_sha)

    filter_callback = None
    if tag_filter:
        filter_callback = create_tag_filter(tag_filter, package_name=package_name, root=root)

    log.log(INFO, "Getting latest tag")
    log.log(DEBUG, "Sorting tags by %r", sort_by)
    tag = get_tag(sort_by=sort_by, root=root, filter_callback=filter_callback)
    if not tag:
        log.log(INFO, "No tags found")
        tag_sha = None
        on_tag = False
    else:
        tag_sha = get_sha(tag, root=root)
        log.log(INFO, "Tag SHA-256: %r", tag_sha)

        on_tag = head_sha is not None and head_sha == tag_sha
        log.log(INFO, "HEAD is tagged: %r", on_tag)

    if version_file:
        if prefer_tag and tag is not None:
            log.log(
                INFO,
                "Both 'version_file' and a Git tag (%r) are present, and 'prefer_tag' is enabled: using the tag",
                tag,
            )
            if tag_sha is None:
                tag_sha = get_sha(tag, root=root)
                log.log(DEBUG, "Tag SHA-256: %r", tag_sha)
            on_tag = head_sha is not None and tag_sha is not None and head_sha == tag_sha
            file_tag = None
            version_file_path = project_root.joinpath(version_file)
            if version_file_path.exists():
                file_tag = version_file_path.read_text().strip() or None
            if file_tag and file_tag.lstrip("v") != tag.lstrip("v"):
                log.warning(
                    "Git tag %r and 'version_file' content %r are different: using the tag. "
                    "Update the version file to silence this warning",
                    tag,
                    file_tag,
                )
            ccount = count_since(tag_sha, root=root) if tag_sha else None
            log.log(INFO, "Commits count between HEAD and last tag: %r", ccount)

            if tag_formatter is not None:
                tag_format_callback = create_tag_formatter(tag_formatter, package_name=package_name, root=root)
                tag = tag_format_callback(tag)
                log.log(DEBUG, "Tag after formatting: %r", tag)
        else:
            log.log(INFO, "Checking for 'version_file'")

            version_file_path = project_root.joinpath(version_file)
            if not version_file_path.exists():
                log.log(
                    INFO,
                    "version_file '%s' does not exist, return starting_version %r",
                    version_file_path,
                    starting_version,
                )
                tag = None
            else:
                log.log(INFO, "Reading version_file '%s' content", version_file)
                tag = version_file_path.read_text().strip() or None

                if not tag:
                    log.log(INFO, "File %r is empty", version_file)
                else:
                    log.log(DEBUG, "File content: %r", tag)

                    if not count_commits_from_version_file:
                        return sanitize_version(tag)

                    file_sha = get_latest_file_commit(version_file, root=root)
                    log.log(DEBUG, "File SHA-256: %r", file_sha)

                    ccount = count_since(file_sha, root=root) if file_sha else None
                    log.log(INFO, "Commits count between HEAD and last version file change: %r", ccount)

    elif not head_sha:
        log.log(INFO, "Not a git repo, or repo without any branch")

    elif tag_sha:
        ccount = count_since(tag_sha, root=root)
        log.log(INFO, "Commits count between HEAD and last tag: %r", ccount)

        if tag_formatter is not None:
            tag_format_callback = create_tag_formatter(tag_formatter, package_name=package_name, root=root)
            tag = tag_format_callback(tag)
            log.log(DEBUG, "Tag after formatting: %r", tag)

    if not tag:
        log.log(INFO, "No source for version, return starting_version %r", starting_version)
        return sanitize_version(starting_version)

    dirty = is_dirty(root=root)
    log.log(INFO, "Is dirty: %r", dirty)

    branch = get_branch(root=root)
    log.log(INFO, "Current branch: %r", branch)

    if branch_formatter is not None and branch is not None:
        branch_format_callback = create_branch_formatter(branch_formatter, package_name=package_name, root=root)
        branch = branch_format_callback(branch)
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

    full_sha = head_sha if head_sha is not None else ""
    version = resolve_substitutions(t, sha=full_sha[:8], tag=tag, ccount=ccount or 0, branch=branch, full_sha=full_sha)
    log.log(INFO, "Version number after resolving substitutions: %r", version)
    return sanitize_version(version)
