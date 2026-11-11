from __future__ import annotations

import shutil
import tarfile
from typing import TYPE_CHECKING

import pytest
from packaging.version import Version

from setuptools_git_versioning.archival import (
    ARCHIVAL_FILENAME,
    ArchivalData,
    get_data_from_archival_file,
    parse_archival_file,
    version_from_archival,
)
from tests.lib.util import (
    create_file,
    create_tag,
    execute,
    get_version,
)

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.all

GIT_ARCHIVAL_STABLE = "node: $Format:%H$\ndescribe-name: $Format:%(describe:tags=true,match=*[0-9]*)$\n"
GIT_ARCHIVAL_WITH_BRANCH = (
    "node: $Format:%H$\ndescribe-name: $Format:%(describe:tags=true,match=*[0-9]*)$\nref-names: $Format:%D$\n"
)


# ---------------------------------------------------------------------------
# Unit tests: parse_archival_file + archival_to_version_data
# ---------------------------------------------------------------------------


def test_parse_archival_file_round_trip(tmp_path: Path) -> None:
    archival = tmp_path / ARCHIVAL_FILENAME
    archival.write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\n"
        "describe-name: v1.2.3-5-g4060507deadbeef0123456789abcdef012345678\n"
        "ref-names: HEAD -> main, tag: v1.2.3\n",
        encoding="utf-8",
    )

    data = parse_archival_file(archival)
    assert data["node"] == "4060507deadbeef0123456789abcdef012345678"
    assert data["describe-name"] == "v1.2.3-5-g4060507deadbeef0123456789abcdef012345678"
    assert data["ref-names"] == "HEAD -> main, tag: v1.2.3"


def test_parse_archival_file_warns_on_content_after_blank_line(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A blank line in the file ends MIME header parsing. Anything after
    it would be silently lost; the parser should warn instead."""
    archival = tmp_path / ARCHIVAL_FILENAME
    archival.write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\n"
        "describe-name: v1.2.3\n"
        "\n"
        "ref-names: HEAD -> main, tag: v1.2.3\n",
        encoding="utf-8",
    )

    with caplog.at_level("WARNING"):
        data = parse_archival_file(archival)

    assert "ref-names" not in data
    assert "after a blank line" in caplog.text


def test_parse_archival_file_normalizes_keys_to_lowercase(tmp_path: Path) -> None:
    """Keys in .git_archival.txt should be looked up case-insensitively;
    parse_archival_file normalizes them to lowercase."""
    archival = tmp_path / ARCHIVAL_FILENAME
    archival.write_text(
        "Node: 4060507deadbeef0123456789abcdef012345678\nDescribe-Name: v1.2.3\n",
        encoding="utf-8",
    )

    data = parse_archival_file(archival)
    assert data["node"] == "4060507deadbeef0123456789abcdef012345678"
    assert data["describe-name"] == "v1.2.3"


def test_archival_to_version_data_post_tag() -> None:
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "v1.2.3-5-g4060507deadbeef0123456789abcdef012345678",
    }
    result = get_data_from_archival_file(data)
    assert result == ArchivalData(
        tag="v1.2.3",
        ccount=5,
        sha="4060507d",
        full_sha="4060507deadbeef0123456789abcdef012345678",
        dirty=False,
        branch=None,
    )


def test_archival_to_version_data_bare_tag() -> None:
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "v1.2.3",
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.tag == "v1.2.3"
    assert result.ccount == 0
    assert result.full_sha == "4060507deadbeef0123456789abcdef012345678"
    assert result.sha == "4060507d"
    assert result.dirty is False


def test_archival_to_version_data_dirty_suffix() -> None:
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "v1.2.3-5-g4060507deadbeef0123456789abcdef012345678-dirty",
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.dirty is True
    assert result.tag == "v1.2.3"
    assert result.ccount == 5


def test_archival_to_version_data_unsubstituted_returns_none(caplog: pytest.LogCaptureFixture) -> None:
    data = {"node": "$Format:%H$", "describe-name": "$Format:%(describe)$"}
    with caplog.at_level("WARNING"):
        result = get_data_from_archival_file(data)
    assert result is None
    assert "unprocessed" in caplog.text


def test_archival_to_version_data_old_git_falls_back_to_ref_names(
    caplog: pytest.LogCaptureFixture,
) -> None:
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "%(describe:tags=true,match=*[0-9]*)",
        "ref-names": "HEAD -> main, tag: v1.2.3",
    }
    with caplog.at_level("WARNING"):
        result = get_data_from_archival_file(data)
    assert result is not None
    assert result.tag == "v1.2.3"
    assert result.ccount == 0
    assert "git <2.32" in caplog.text


def test_archival_to_version_data_old_git_no_tag_in_ref_names_returns_none(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Old-git fallback path: describe-name is unexpanded AND ref-names
    has no `tag:` entry. The function should warn about the old-git
    fallback and then return None.
    """
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "%(describe:tags=true,match=*[0-9]*)",
        "ref-names": "HEAD -> main, origin/main",
    }
    with caplog.at_level("WARNING"):
        result = get_data_from_archival_file(data)
    assert result is None
    assert "git <2.32" in caplog.text


def test_archival_to_version_data_accepts_sha256_node() -> None:
    """SHA-256 git repositories produce 64-char node hashes. The parser
    should accept them and use them as full_sha just like 40-char SHA-1.
    """
    sha256_node = "4060507deadbeef0123456789abcdef0123456789abcdef0123456789abcdef0"
    data = {
        "node": sha256_node,
        "describe-name": "v1.2.3",
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.tag == "v1.2.3"
    assert result.full_sha == sha256_node
    assert result.sha == sha256_node[:8]


def test_archival_to_version_data_prefers_full_sha_over_describe_short_sha() -> None:
    """When both `node` (40 chars) and describe-name's short SHA (7 chars)
    are present, `sha` should be the 8-char prefix of `node`, matching the
    live-git path's `full_sha[:8]` rendering rather than the truncated
    short SHA from describe-name.
    """
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "v1.2.3-5-g4060507",  # conventional 7-char short SHA
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.tag == "v1.2.3"
    assert result.ccount == 5
    assert result.sha == "4060507d"  # 8 chars from node, not 7-char "4060507"
    assert result.full_sha == "4060507deadbeef0123456789abcdef012345678"


def test_archival_to_version_data_describe_with_non_numeric_middle_part() -> None:
    """When a describe-name happens to rsplit into 3 parts but the middle
    part is non-numeric (e.g., a tag like `foo-bar-baz`), the function
    should fall back to treating the whole string as a bare tag rather
    than crashing on int() conversion.
    """
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "foo-bar-baz",
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.tag == "foo-bar-baz"
    assert result.ccount == 0


@pytest.mark.parametrize("tag", ["2024-01-15", "v2024-01-15", "1.2.3-4-gamma"])
def test_archival_to_version_data_bare_tag_resembling_describe_suffix(tag: str) -> None:
    """For a commit exactly on a tag, describe-name is the bare tag. A tag
    whose last two hyphen-separated parts merely resemble the `-N-gSHA`
    suffix (e.g., a date) must not be split into tag, ccount and SHA.
    """
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": tag,
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.tag == tag
    assert result.ccount == 0
    assert result.sha == "4060507d"


def test_archival_to_version_data_hyphenated_tag_post_tag() -> None:
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "2024-01-15-3-g4060507",
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.tag == "2024-01-15"
    assert result.ccount == 3


def test_archival_to_version_data_short_sha_fallback_when_node_missing() -> None:
    """When `node` is absent/invalid, full_sha should fall back to the
    short SHA from describe-name (best-effort)."""
    data = {
        "describe-name": "v1.2.3-5-gabc1234",
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.tag == "v1.2.3"
    assert result.ccount == 5
    assert result.sha == "abc1234"
    assert result.full_sha == "abc1234"


def test_archival_to_version_data_branch_from_ref_names() -> None:
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "v1.2.3-5-g4060507deadbeef0123456789abcdef012345678",
        "ref-names": "HEAD -> feature/x, origin/main",
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.branch == "feature/x"


def test_archival_to_version_data_branch_absent() -> None:
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "describe-name": "v1.2.3-5-g4060507deadbeef0123456789abcdef012345678",
    }
    result = get_data_from_archival_file(data)
    assert result is not None
    assert result.branch is None


def test_archival_to_version_data_no_tag_anywhere_returns_none() -> None:
    data = {
        "node": "4060507deadbeef0123456789abcdef012345678",
        "ref-names": "HEAD -> main",
    }
    assert get_data_from_archival_file(data) is None


def test_version_from_archival_missing_file_returns_none(tmp_path: Path) -> None:
    assert version_from_archival(tmp_path) is None


def test_version_from_archival_post_tag(tmp_path: Path) -> None:
    (tmp_path / ARCHIVAL_FILENAME).write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\n"
        "describe-name: v1.2.3-5-g4060507deadbeef0123456789abcdef012345678\n",
        encoding="utf-8",
    )
    version = version_from_archival(tmp_path)
    assert version == Version("1.2.3.post5+git.4060507d")


def test_version_from_archival_bare_tag_uses_template(tmp_path: Path) -> None:
    (tmp_path / ARCHIVAL_FILENAME).write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\ndescribe-name: v1.2.3\n",
        encoding="utf-8",
    )
    version = version_from_archival(tmp_path)
    assert version == Version("1.2.3")


def test_version_from_archival_dirty(tmp_path: Path) -> None:
    (tmp_path / ARCHIVAL_FILENAME).write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\n"
        "describe-name: v1.2.3-5-g4060507deadbeef0123456789abcdef012345678-dirty\n",
        encoding="utf-8",
    )
    version = version_from_archival(tmp_path)
    assert version == Version("1.2.3.post5+git.4060507d.dirty")


def test_version_from_archival_branch_defaults_to_head_when_missing(tmp_path: Path) -> None:
    (tmp_path / ARCHIVAL_FILENAME).write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\n"
        "describe-name: v1.2.3-5-g4060507deadbeef0123456789abcdef012345678\n",
        encoding="utf-8",
    )
    version = version_from_archival(
        tmp_path,
        dev_template="{tag}.post{ccount}+git.{sha}.{branch}",
    )
    assert version == Version("1.2.3.post5+git.4060507d.HEAD")


def test_version_from_archival_applies_tag_formatter(tmp_path: Path) -> None:
    (tmp_path / ARCHIVAL_FILENAME).write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\ndescribe-name: release/1.2.3\n",
        encoding="utf-8",
    )
    version = version_from_archival(
        tmp_path,
        tag_formatter=lambda tag: tag[len("release/") :] if tag.startswith("release/") else tag,
    )
    assert version == Version("1.2.3")


def test_version_from_archival_applies_branch_formatter(tmp_path: Path) -> None:
    (tmp_path / ARCHIVAL_FILENAME).write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\n"
        "describe-name: v1.2.3-5-g4060507deadbeef0123456789abcdef012345678\n"
        "ref-names: HEAD -> feature/issue-1234-add-a-great-feature\n",
        encoding="utf-8",
    )
    version = version_from_archival(
        tmp_path,
        dev_template="{tag}.post{ccount}+{branch}",
        branch_formatter=lambda branch: branch.split("/")[1].split("-")[1],
    )
    assert version == Version("1.2.3.post5+1234")


# ---------------------------------------------------------------------------
# Integration: real `git archive` round-trip + build
# ---------------------------------------------------------------------------


def _add_archival_template(repo: Path, *, include_ref_names: bool = False) -> None:
    template = GIT_ARCHIVAL_WITH_BRANCH if include_ref_names else GIT_ARCHIVAL_STABLE
    create_file(repo, ARCHIVAL_FILENAME, template, commit=False)
    create_file(repo, ".gitattributes", f"{ARCHIVAL_FILENAME}  export-subst\n", commit=False)
    execute(repo, "git", "add", ARCHIVAL_FILENAME, ".gitattributes")
    execute(repo, "git", "commit", "-m", "add git archive support")


def _git_archive_extract(repo: Path, dest: Path) -> None:
    archive = repo / "archive.tar"
    execute(repo, "git", "archive", "--format=tar", f"--output={archive}", "HEAD")
    with tarfile.open(archive, "r") as tf:
        tf.extractall(dest)
    archive.unlink()


@pytest.mark.important
def test_archival_end_to_end_post_tag(repo: Path, tmp_path_factory: pytest.TempPathFactory, create_config) -> None:
    create_config(repo, {"dev_template": "{tag}.post{ccount}"})
    create_tag(repo, "1.2.3")
    create_file(repo)  # one commit after the tag
    _add_archival_template(repo)

    extracted = tmp_path_factory.mktemp("extracted")
    _git_archive_extract(repo, extracted)
    assert not (extracted / ".git").exists()

    archival_text = (extracted / ARCHIVAL_FILENAME).read_text(encoding="utf-8")
    assert "$Format:" not in archival_text  # placeholders were substituted

    # Carry over coverage config so the integration test contributes coverage data
    shutil.copy(repo / ".coveragerc", extracted / ".coveragerc")

    assert get_version(extracted) == "1.2.3.post2"


@pytest.mark.important
def test_archival_end_to_end_dirty(repo: Path, tmp_path_factory: pytest.TempPathFactory, create_config) -> None:
    """When the archival file's describe-name carries a `-dirty` suffix,
    the dirty_template is used.

    Note: `git archive` itself cannot produce a `-dirty` describe-name.
    It archives the committed tree (working-tree modifications are not
    included), and the `%(describe:...)` placeholder is evaluated against
    the archived commit, not the working tree - so dirtying the repo
    before `git archive` has no effect on the substituted output.
    The `-dirty` suffix only reaches the archival file if a user
    generates it outside `git archive` (e.g., `git describe --dirty
    > .git_archival.txt`) or hand-edits it. We simulate that here by
    patching the extracted file.
    """
    create_config(repo, {"dirty_template": "{tag}.post{ccount}+dirty"})
    create_tag(repo, "1.2.3")
    create_file(repo)
    _add_archival_template(repo)

    extracted = tmp_path_factory.mktemp("extracted")
    _git_archive_extract(repo, extracted)

    archival_path = extracted / ARCHIVAL_FILENAME
    lines = archival_path.read_text(encoding="utf-8").splitlines()
    patched = [(line + "-dirty") if line.startswith("describe-name:") else line for line in lines]
    archival_path.write_text("\n".join(patched) + "\n", encoding="utf-8")

    shutil.copy(repo / ".coveragerc", extracted / ".coveragerc")

    # ccount=2: one post-tag commit + the archival-template commit
    assert get_version(extracted) == "1.2.3.post2+dirty"


@pytest.mark.important
def test_archival_end_to_end_bare_tag(repo: Path, tmp_path_factory: pytest.TempPathFactory, create_config) -> None:
    create_config(repo, {"template": "{tag}"})
    _add_archival_template(repo)
    create_tag(repo, "1.2.3")

    extracted = tmp_path_factory.mktemp("extracted")
    _git_archive_extract(repo, extracted)
    shutil.copy(repo / ".coveragerc", extracted / ".coveragerc")

    assert get_version(extracted) == "1.2.3"


@pytest.mark.important
def test_archival_end_to_end_bare_hyphenated_tag(
    repo: Path,
    tmp_path_factory: pytest.TempPathFactory,
    create_config,
) -> None:
    create_config(repo, {"template": "{tag}"})
    _add_archival_template(repo)
    create_tag(repo, "2024-01-15")
    assert get_version(repo) == "2024.1.15"

    extracted = tmp_path_factory.mktemp("extracted")
    _git_archive_extract(repo, extracted)
    shutil.copy(repo / ".coveragerc", extracted / ".coveragerc")

    assert get_version(extracted) == "2024.1.15"


@pytest.mark.important
def test_archival_end_to_end_tag_formatter(repo: Path, tmp_path_factory: pytest.TempPathFactory, create_config) -> None:
    create_file(
        repo,
        "util.py",
        "def tag_formatter(tag):\n    return tag[len('release/'):] if tag.startswith('release/') else tag\n",
    )
    create_config(
        repo,
        {
            "tag_formatter": "util:tag_formatter",
        },
    )
    _add_archival_template(repo)
    create_tag(repo, "release/1.2.3")

    extracted = tmp_path_factory.mktemp("extracted")
    _git_archive_extract(repo, extracted)
    shutil.copy(repo / ".coveragerc", extracted / ".coveragerc")

    assert get_version(extracted) == "1.2.3"


@pytest.mark.important
def test_archival_end_to_end_branch_formatter(
    repo: Path,
    tmp_path_factory: pytest.TempPathFactory,
    create_config,
) -> None:
    create_tag(repo, "1.2.3")
    create_file(repo)  # one commit after the tag
    execute(repo, "git", "checkout", "-b", "feature/issue-1234-add-a-great-feature")
    create_file(
        repo,
        "util.py",
        "def branch_formatter(branch):\n    return branch.split('/')[1].split('-')[1]\n",
    )
    create_config(
        repo,
        {
            "dev_template": "{tag}.post{ccount}+{branch}",
            "branch_formatter": "util:branch_formatter",
        },
    )
    _add_archival_template(repo, include_ref_names=True)

    extracted = tmp_path_factory.mktemp("extracted")
    _git_archive_extract(repo, extracted)
    shutil.copy(repo / ".coveragerc", extracted / ".coveragerc")

    assert get_version(extracted) == "1.2.3.post4+1234"


def test_archival_unsubstituted_falls_through_to_live_git(repo: Path, caplog: pytest.LogCaptureFixture) -> None:
    """When the .git_archival.txt file is read inside a working checkout
    (placeholders not yet expanded), the archival path should warn and fall
    through to the live-git flow.
    """
    create_file(repo, ARCHIVAL_FILENAME, GIT_ARCHIVAL_STABLE)
    create_tag(repo, "1.2.3")

    from setuptools_git_versioning.version import version_from_git

    with caplog.at_level("WARNING"):
        version = version_from_git(root=repo)
    assert version == Version("1.2.3")
    assert "unprocessed" in caplog.text


def test_archival_priority_pkg_info_still_wins(tmp_path_factory: pytest.TempPathFactory) -> None:
    """When PKG-INFO is present (sdist), it takes precedence over .git_archival.txt."""
    project = tmp_path_factory.mktemp("sdist")
    (project / "PKG-INFO").write_text("Version: 9.9.9\n", encoding="utf-8")
    (project / ARCHIVAL_FILENAME).write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\ndescribe-name: v1.2.3\n",
        encoding="utf-8",
    )
    from setuptools_git_versioning.version import version_from_git

    assert version_from_git(root=project) == Version("9.9.9")


def test_archival_priority_before_live_git(tmp_path_factory: pytest.TempPathFactory) -> None:
    """When .git_archival.txt is present and there's no .git, the archival result is used."""
    project = tmp_path_factory.mktemp("archive_no_git")
    (project / ARCHIVAL_FILENAME).write_text(
        "node: 4060507deadbeef0123456789abcdef012345678\n"
        "describe-name: v1.2.3-5-g4060507deadbeef0123456789abcdef012345678\n",
        encoding="utf-8",
    )
    from setuptools_git_versioning.version import version_from_git

    assert version_from_git(root=project) == Version("1.2.3.post5+git.4060507d")
