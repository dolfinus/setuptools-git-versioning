from __future__ import annotations

import logging
import os  # noqa: TC003
import re
from dataclasses import dataclass
from email.parser import HeaderParser
from pathlib import Path
from typing import TYPE_CHECKING

from setuptools_git_versioning.defaults import (
    DEFAULT_DEV_TEMPLATE,
    DEFAULT_DIRTY_TEMPLATE,
    DEFAULT_TEMPLATE,
)
from setuptools_git_versioning.factories import create_branch_formatter, create_tag_formatter
from setuptools_git_versioning.log import DEBUG, INFO
from setuptools_git_versioning.subst import resolve_substitutions

if TYPE_CHECKING:
    from typing import Callable

    from packaging.version import Version

ARCHIVAL_FILENAME = ".git_archival.txt"
DESCRIBE_UNSUPPORTED = "%(describe"
FORMAT_UNSUBSTITUTED = "$Format"

DESCRIBE_RE = re.compile(r"^(?P<tag>.+)-(?P<ccount>[0-9]+)-g(?P<sha>[0-9a-f]+)$")  # tag-N-gSHA
REF_TAG_RE = re.compile(r"(?<=\btag: )([^,]+)\b")
REF_HEAD_RE = re.compile(r"HEAD\s*->\s*([^,]+)")
FULL_SHA_RE = re.compile(r"^([0-9a-f]{40}|[0-9a-f]{64})$")  # SHA-1 or SHA-256

log = logging.getLogger(__name__)


@dataclass
class ArchivalData:
    tag: str
    ccount: int
    sha: str
    full_sha: str
    dirty: bool
    branch: str | None


def parse_archival_file(path: str | os.PathLike) -> dict[str, str]:
    """Read a .git_archival.txt file and return its key/value pairs.

    Keys are normalized to lowercase so lookups behave consistently
    regardless of whether the file uses `node:` or `Node:` etc.
    """
    content = Path(path).read_text(encoding="utf-8")
    log.log(DEBUG, "'%s' content:\n%s", ARCHIVAL_FILENAME, content)
    message = HeaderParser().parsestr(content)

    # HeaderParser treats the first blank line as the end of headers.
    # Anything after it ends up in the message body and is silently
    # dropped from .items(). Warn the user instead of losing fields.
    payload = message.get_payload()
    if isinstance(payload, str) and payload.strip():
        log.warning(
            "'%s' contains content after a blank line; those fields will be ignored",
            ARCHIVAL_FILENAME,
        )

    return {key.lower(): value for key, value in message.items()}


def _parse_describe(describe: str) -> tuple[str, int, str | None, bool]:
    """Parse a `git describe`-style string into (tag, ccount, short_sha, dirty)."""
    dirty = False
    if describe.endswith("-dirty"):
        dirty = True
        describe = describe[: -len("-dirty")]

    # On a tagged commit, `git describe` prints the bare tag. Only split off
    # the suffix when it really is `-N-gSHA`, so that tags like `2024-01-15`
    # are not mistaken for a tag followed by a commit count and a SHA.
    match = DESCRIBE_RE.match(describe)
    if not match:
        return describe, 0, None, dirty

    return match.group("tag"), int(match.group("ccount")), match.group("sha"), dirty


def _branch_from_ref_names(ref_names: str) -> str | None:
    match = REF_HEAD_RE.search(ref_names)
    if match:
        return match.group(1).strip()
    return None


def get_data_from_archival_file(data: dict[str, str]) -> ArchivalData | None:
    """Convert parsed archival data into structured version info, or None.

    Returns None when the file looks unsubstituted or otherwise unusable so
    the caller can fall through to live git.
    """
    if any(FORMAT_UNSUBSTITUTED in value for value in data.values()):
        log.warning(
            "'%s' contains unprocessed '$Format:...$' placeholders, skipping",
            ARCHIVAL_FILENAME,
        )
        return None

    node = data.get("node", "").strip()
    full_sha = node if FULL_SHA_RE.match(node) else ""
    ref_names = data.get("ref-names", "")
    branch = _branch_from_ref_names(ref_names)
    describe = data.get("describe-name", "").strip()

    describe_tag: str | None = None
    ccount = 0
    short_sha = ""
    dirty = False

    if describe and DESCRIBE_UNSUPPORTED not in describe:
        describe_tag, ccount, parsed_sha, dirty = _parse_describe(describe)
        if parsed_sha:
            short_sha = parsed_sha
    elif describe:
        log.warning(
            "git archive did not expand %(describe...) (git <2.32), falling back to ref-names",
        )

    if describe_tag is not None:
        tag = describe_tag
    else:
        tags = REF_TAG_RE.findall(ref_names)
        if not tags:
            log.log(
                INFO,
                "'%s' has no usable describe-name or tag in ref-names",
                ARCHIVAL_FILENAME,
            )
            return None
        tag = tags[0].strip()

    # Prefer the full SHA when available so {sha} matches the live-git
    # path's `full_sha[:8]` rendering. Fall back to the short SHA from
    # describe-name only when no valid `node` field is present.
    if full_sha:
        short_sha = full_sha[:8]
    elif short_sha:
        full_sha = short_sha

    return ArchivalData(
        tag=tag,
        ccount=ccount,
        sha=short_sha[:8],
        full_sha=full_sha,
        dirty=dirty,
        branch=branch,
    )


def version_from_archival(  # noqa: PLR0913
    project_root: str | os.PathLike,
    *,
    package_name: str | None = None,
    template: str = DEFAULT_TEMPLATE,
    dev_template: str = DEFAULT_DEV_TEMPLATE,
    dirty_template: str = DEFAULT_DIRTY_TEMPLATE,
    tag_formatter: Callable[[str], str] | str | None = None,
    branch_formatter: Callable[[str], str] | str | None = None,
) -> Version | None:
    """Return a Version derived from .git_archival.txt, or None if unavailable."""
    archival_path = Path(project_root).joinpath(ARCHIVAL_FILENAME)
    if not archival_path.exists():
        log.log(DEBUG, "No '%s' present at '%s'", ARCHIVAL_FILENAME, project_root)
        return None

    log.log(INFO, "File '%s' is found, reading its content", archival_path)
    data = parse_archival_file(archival_path)
    info = get_data_from_archival_file(data)
    if info is None:
        return None

    log.log(DEBUG, "Parsed archival data: %r", info)

    tag = info.tag
    if tag_formatter is not None:
        tag_format_callback = create_tag_formatter(tag_formatter, package_name=package_name, root=project_root)
        tag = tag_format_callback(tag)
        log.log(DEBUG, "Tag after formatting: %r", tag)

    if info.dirty:
        log.log(INFO, "Using template from 'dirty_template' option")
        chosen = dirty_template
    elif info.ccount > 0:
        log.log(INFO, "Using template from 'dev_template' option")
        chosen = dev_template
    else:
        log.log(INFO, "Using template from 'template' option")
        chosen = template

    # When ref-names is absent or doesn't reveal a current branch, default
    # to the literal "HEAD" so `{branch}` substitution mirrors what
    # `git rev-parse --abbrev-ref HEAD` produces in detached-HEAD state.
    branch = info.branch if info.branch is not None else "HEAD"
    if branch_formatter is not None:
        branch_format_callback = create_branch_formatter(branch_formatter, package_name=package_name, root=project_root)
        branch = branch_format_callback(branch)
        log.log(INFO, "Branch after formatting: %r", branch)

    rendered = resolve_substitutions(
        chosen,
        sha=info.sha,
        tag=tag,
        ccount=info.ccount,
        branch=branch,
        full_sha=info.full_sha,
    )
    log.log(INFO, "Version number after resolving substitutions: %r", rendered)

    # Deferred to avoid a top-level circular import:
    # `version.py` imports `version_from_archival` from this module.
    from setuptools_git_versioning.version import sanitize_version

    return sanitize_version(rendered)
