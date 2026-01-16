from __future__ import annotations

import logging
import os
import subprocess  # nosec
from contextlib import suppress
from pathlib import Path
from typing import Callable

from setuptools_git_versioning.defaults import DEFAULT_SORT_BY
from setuptools_git_versioning.log import DEBUG

log = logging.getLogger(__name__)


def _exec(*cmd: str, root: str | os.PathLike | None = None) -> list[str]:
    log.log(DEBUG, "Executing %r at '%s'", cmd, root or Path.cwd())
    try:
        stdout = subprocess.check_output(cmd, text=True, cwd=root)  # noqa: S603
    except subprocess.CalledProcessError as e:
        stdout = e.output
    except (FileNotFoundError, OSError) as e:
        # Handle case where git executable is not found
        # FileNotFoundError on Unix, OSError on some other systems
        log.log(DEBUG, "Command not found: %r", e)
        stdout = ""
    lines = stdout.splitlines()
    return [line.rstrip() for line in lines if line.rstrip()]


def get_branches(root: str | os.PathLike | None = None) -> list[str]:
    """Return list of branch names in the git repository"""
    branches = _exec("git", "branch", "-l", "--format", "%(refname:short)", root=root)
    return branches or []


def get_branch(root: str | os.PathLike | None = None) -> str | None:
    """Return branch name pointing to HEAD, or None"""
    branches = _exec("git", "rev-parse", "--abbrev-ref", "HEAD", root=root)
    return branches[0] if branches else None


def get_all_tags(sort_by: str = DEFAULT_SORT_BY, root: str | os.PathLike | None = None) -> list[str]:
    """Return list of tags in the git repository"""
    tags = _exec("git", "tag", f"--sort=-{sort_by}", root=root)
    return tags or []


def get_tags(
    sort_by: str = DEFAULT_SORT_BY,
    filter_callback: Callable[[str], str | None] | None = None,
    root: str | os.PathLike | None = None,
) -> list[str]:
    """Return list of tags merged into HEAD history tree"""
    tags = _exec("git", "tag", f"--sort=-{sort_by}", "--merged", root=root)
    if filter_callback:
        # pull the tags that don't start with tag_prefix out of the list
        return list(filter(filter_callback, tags))
    return tags or []


def get_tag(*args, **kwargs) -> str | None:
    """Return latest tag merged into HEAD history tree"""
    tags = get_tags(*args, **kwargs)
    return tags[0] if tags else None


def get_sha(name: str = "HEAD", root: str | os.PathLike | None = None) -> str | None:
    """Get commit SHA-1 hash"""
    sha = _exec("git", "rev-list", "-n", "1", name, root=root)
    return sha[0] if sha else None


def get_latest_file_commit(path: str | os.PathLike, root: str | os.PathLike | None = None) -> str | None:
    """Get SHA-1 hash of latest commit of the file in the repository"""
    sha = _exec("git", "log", "-n", "1", "--pretty=format:%H", "--", os.fspath(path), root=root)
    return sha[0] if sha else None


def is_dirty(root: str | os.PathLike | None = None) -> bool:
    """Check index status, and return True if there are some uncommitted changes"""
    res = _exec("git", "status", "--short", root=root)
    return bool(res)


def count_since(name: str, root: str | os.PathLike | None = None) -> int | None:
    """Get number of commits between HEAD and the commit, or None if they are not related"""
    res = _exec("git", "rev-list", "--count", "HEAD", f"^{name}", root=root)
    if res:
        with suppress(ValueError, TypeError):
            return int(res[0])
    return None
