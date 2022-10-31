import subprocess
from datetime import datetime, timedelta
import pytest
import time

from tests.lib.util import (
    create_file,
    get_full_sha,
    get_version,
    get_sha,
    create_tag,
    checkout_branch,
    create_commit,
)

pytestmark = pytest.mark.all


@pytest.mark.important
@pytest.mark.flaky(reruns=3)  # sha and full_sha can start with 0 which are removed, just try again
@pytest.mark.parametrize(
    "template, subst",
    [
        (None, "1.0.0"),
        ("{tag}.post{ccount}+git.{full_sha}", "1.0.0.post0+git.{full_sha}"),
        ("{tag}.post{ccount}+git.{sha}", "1.0.0.post0+git.{sha}"),
        ("{tag}.post{ccount}", "1.0.0.post0"),
        ("{tag}", "1.0.0"),
    ],
)
def test_tag(repo, create_config, template, subst):
    if template:
        create_config(repo, {"template": template})
    else:
        create_config(repo)

    create_tag(repo, "1.0.0")

    full_sha = get_full_sha(repo)
    sha = get_sha(repo)
    assert get_version(repo) == subst.format(sha=sha, full_sha=full_sha)


@pytest.mark.flaky(reruns=3)  # sha and full_sha can start with 0 which are removed, just try again
@pytest.mark.parametrize(
    "template, subst",
    [
        (None, "1.0.0.post1+git.{sha}"),
        ("{tag}.post{ccount}+git.{full_sha}", "1.0.0.post1+git.{full_sha}"),
        ("{tag}.post{ccount}+git.{sha}", "1.0.0.post1+git.{sha}"),
        ("{tag}.post{ccount}", "1.0.0.post1"),
        ("{tag}", "1.0.0"),
    ],
)
def test_tag_dev(repo, create_config, template, subst):
    if template:
        create_config(repo, {"dev_template": template})
    else:
        create_config(repo)

    create_tag(repo, "1.0.0")
    create_file(repo)

    full_sha = get_full_sha(repo)
    sha = get_sha(repo)
    assert get_version(repo) == subst.format(sha=sha, full_sha=full_sha)


@pytest.mark.flaky(reruns=3)  # sha and full_sha can start with 0 which are removed, just try again
@pytest.mark.parametrize(
    "template, subst",
    [
        (None, "1.0.0.post0+git.{sha}.dirty"),
        ("{tag}.post{ccount}+git.{full_sha}.dirty", "1.0.0.post0+git.{full_sha}.dirty"),
        ("{tag}.post{ccount}+git.{sha}.dirty", "1.0.0.post0+git.{sha}.dirty"),
        ("{tag}.post{ccount}+dirty", "1.0.0.post0+dirty"),
        ("{tag}+dirty", "1.0.0+dirty"),
    ],
)
@pytest.mark.parametrize("add", [True, False])
def test_tag_dirty(repo, create_config, add, template, subst):
    if template:
        create_config(repo, {"dirty_template": template})
    else:
        create_config(repo)

    create_tag(repo, "1.0.0")
    create_file(repo, add=add, commit=False)

    full_sha = get_full_sha(repo)
    sha = get_sha(repo)
    assert get_version(repo) == subst.format(sha=sha, full_sha=full_sha)


@pytest.mark.parametrize("starting_version, version", [(None, "0.0.1"), ("1.2.3", "1.2.3")])
def test_tag_missing(repo, create_config, starting_version, version):
    if starting_version:
        create_config(repo, {"starting_version": starting_version})
    else:
        create_config(repo)

    assert get_version(repo) == version


@pytest.mark.parametrize(
    "tag, version",
    [
        ("1.0.0", "1.0.0"),
        ("v1.2.3", "1.2.3"),
        ("1.2.3dev1", "1.2.3.dev1"),
        ("1.2.3.dev1", "1.2.3.dev1"),
        ("1.2.3-dev1", "1.2.3.dev1"),
        ("1.2.3+local", "1.2.3+local"),
        ("1.2.3+local-abc", "1.2.3+local.abc"),
        ("1.2.3+local_abc", "1.2.3+local.abc"),
        ("1.2.3+local/abc", "1.2.3+local.abc"),
        ("1.2.3+local/abc/-", "1.2.3+local.abc"),
    ],
)
def test_tag_sanitization(repo, create_config, tag, version):
    create_config(repo)
    create_tag(repo, tag)

    assert get_version(repo) == version


@pytest.mark.parametrize(
    "tag",
    [
        "alpha1.0.0",
        "1.0.0abc",
        "1.0.0.abc",
        "1.0.0-abc",
        "1.0.0_abc",
    ],
)
def test_tag_wrong_version_number(repo, tag, create_config):
    create_config(repo)
    create_tag(repo, tag)

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)


@pytest.mark.parametrize(
    "starting_version",
    [
        "alpha1.0.0",
        "1.0.0abc",
        "1.0.0.abc",
        "1.0.0-abc",
        "1.0.0_abc",
    ],
)
def test_tag_wrong_starting_version(repo, create_config, starting_version):
    create_config(repo, {"starting_version": starting_version})

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)


def test_tag_not_a_repo(repo_dir, create_config):
    create_config(repo_dir, add=False, commit=False)

    assert get_version(repo_dir) == "0.0.1"


def test_tag_non_linear_history(repo, create_config):
    checkout_branch(repo, "dev")
    create_file(repo, commit=False)
    create_config(repo)

    checkout_branch(repo, "master", new=False)
    create_file(repo, commit=False)
    create_config(repo)
    create_tag(repo, "1.0.0")

    checkout_branch(repo, "dev", new=False)
    create_file(repo)
    assert get_version(repo) == "0.0.1"


def test_tag_linear_history(repo, create_config):
    create_tag(repo, "1.0.0")
    checkout_branch(repo, "dev")
    create_config(repo)

    sha = get_sha(repo)
    assert get_version(repo) == f"1.0.0.post1+git.{sha}"


@pytest.mark.parametrize(
    "starting_version",
    [
        "1.0.0",
        "1.2.3",
    ],
)
def test_tag_missing_with_starting_version(repo, create_config, starting_version):
    create_config(repo, {"starting_version": starting_version})

    assert get_version(repo) == starting_version


@pytest.mark.parametrize("message", ["", "Some message"])
def test_tag_sort_by_version(repo, create_config, message):
    sort_by = "version:refname"
    create_config(repo, {"sort_by": sort_by})

    commits = {}

    tags_to_commit = [
        "1.1.0",
        "1.1.10",
        "1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=len(tags_to_commit) - i)
        create_commit(repo, "Some commit", dt=dt)
        commits[tag] = get_sha(repo)

    tags_to_create = [
        "1.1.0",
        "1.1.10",
        "1.1.1",
    ]

    for tag in tags_to_create:
        create_tag(repo, tag, message=message, commit=commits[tag])

    # the result is not stable because latest tag (by name)
    # has nothing in common with commit creation time
    # so it could mess everything up: https://github.com/dolfinus/setuptools-git-versioning/issues/22
    # that's why this value is not default
    assert "1.1.10" in get_version(repo)


@pytest.mark.parametrize("message", ["", "Some message"])
def test_tag_sort_by_commit_date(repo, create_config, message):
    sort_by = "committerdate"
    create_config(repo, {"sort_by": sort_by})

    commits = {}
    tags_to_commit = [
        "1.1.10",
        "1.1.0",
        "1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=len(tags_to_commit) - i)
        create_commit(repo, "Some commit", dt=dt)
        commits[tag] = get_sha(repo)

    tags_to_create = [
        "1.1.0",
        "1.1.1",
        "1.1.10",
    ]

    for tag in tags_to_create:
        create_tag(repo, tag, message=message, commit=commits[tag])

    if not message:
        assert get_version(repo) == "1.1.1"
    else:
        assert get_version(repo).startswith("1.1")
        # the result is totally random because annotaged tags have no such field at all
        # https://github.com/dolfinus/setuptools-git-versioning/issues/23


@pytest.mark.parametrize("message", ["", "Some message"])
def test_tag_sort_by_tag_date(repo, create_config, message):
    sort_by = "taggerdate"
    create_config(repo, {"sort_by": sort_by})

    commits = {}
    tags_to_commit = [
        "1.1.10",
        "1.1.0",
        "1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=len(tags_to_commit) - i)
        create_commit(repo, "Some commit", dt=dt)
        commits[tag] = get_sha(repo)

    tags_to_create = [
        "1.1.0",
        "1.1.1",
        "1.1.10",
    ]

    for tag in tags_to_create:
        create_tag(repo, tag, message=message, commit=commits[tag])
        time.sleep(1)

    if message:
        # the result is not stable because latest tag (by creation time)
        # has nothing in common with commit creation time
        assert "1.1.10" in get_version(repo)
    else:
        assert get_version(repo).startswith("1.1")
        # the result is totally random because annotaged tags have no such field at all
        # https://github.com/dolfinus/setuptools-git-versioning/issues/23


@pytest.mark.parametrize("sort_by", [None, "creatordate"])
@pytest.mark.parametrize("message", ["", "Some message"])
def test_tag_sort_by_create_date(repo, create_config, message, sort_by):
    if sort_by:
        create_config(repo, {"sort_by": sort_by})
    else:
        create_config(repo)

    commits = {}
    tags_to_commit = [
        "1.1.0",
        "1.1.10",
        "1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=len(tags_to_commit) - i)
        create_commit(repo, "Some commit", dt=dt)
        commits[tag] = get_sha(repo)

    tags_to_create = [
        "1.1.10",
        "1.1.1",
        "1.1.0",
    ]

    for tag in tags_to_create:
        create_tag(repo, tag, message=message, commit=commits[tag])

    if message:
        # the result is not stable because latest tag (by creation time)
        # has nothing in common with commit creation time
        # so it is not recommended to create annotated tags in the past
        assert "1.1.0" in get_version(repo)
    else:
        # but at least creatordate field is present in both tag types
        # https://stackoverflow.com/questions/67206124
        # so this is a default value
        assert get_version(repo) == "1.1.1"
