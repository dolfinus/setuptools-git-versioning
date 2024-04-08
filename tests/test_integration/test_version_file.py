import subprocess

import pytest

from tests.lib.util import (
    create_commit,
    create_file,
    create_tag,
    get_full_sha,
    get_sha,
    get_version,
)

pytestmark = pytest.mark.all


@pytest.mark.flaky(reruns=3)  # sha and full_sha can start with 0 which are removed, just try again
@pytest.mark.important
@pytest.mark.parametrize(
    "template",
    [
        None,
        "{tag}.post{ccount}+git.{full_sha}",
    ],
)
def test_version_file(repo, create_config, template):
    config = {
        "version_file": "VERSION.txt",
    }
    if template:
        # template is ignored
        config["dev_template"] = template

    create_config(repo, config)

    create_file(repo, "VERSION.txt", "1.0.0")
    assert get_version(repo) == "1.0.0"

    create_file(repo)
    assert get_version(repo) == "1.0.0"

    create_file(repo, add=True, commit=False)
    assert get_version(repo) == "1.0.0"
    create_commit(repo, "add file")

    create_file(repo, add=False)
    assert get_version(repo) == "1.0.0"


@pytest.mark.flaky(reruns=3)  # sha and full_sha can start with 0 which are removed, just try again
@pytest.mark.parametrize(
    "template, subst",
    [
        (None, "1.0.0.post{ccount}+git.{sha}"),
        ("{tag}.post{ccount}+git.{full_sha}", "1.0.0.post{ccount}+git.{full_sha}"),
        ("{tag}.post{ccount}+git.{sha}", "1.0.0.post{ccount}+git.{sha}"),
        ("{tag}.post{ccount}", "1.0.0.post{ccount}"),
        ("{tag}", "1.0.0"),
    ],
)
def test_version_file_count_commits(repo, create_config, template, subst):
    config = {
        "version_file": "VERSION.txt",
        "count_commits_from_version_file": True,
    }
    if template:
        # template is ignored
        config["dev_template"] = template

    create_config(repo, config)
    create_file(repo, "VERSION.txt", "1.0.0")

    full_sha = get_full_sha(repo)
    sha = get_sha(repo)
    assert get_version(repo) == subst.format(sha=sha, full_sha=full_sha, ccount=0)

    create_file(repo)

    full_sha = get_full_sha(repo)
    sha = get_sha(repo)
    assert get_version(repo) == subst.format(sha=sha, full_sha=full_sha, ccount=1)


@pytest.mark.flaky(reruns=3)  # sha and full_sha can start with 0 which are removed, just try again
@pytest.mark.parametrize(
    "template, subst",
    [
        (None, "1.0.0.post{ccount}+git.{sha}.dirty"),
        ("{tag}.post{ccount}+git.{full_sha}.dirty", "1.0.0.post{ccount}+git.{full_sha}.dirty"),
        ("{tag}.post{ccount}+git.{sha}.dirty", "1.0.0.post{ccount}+git.{sha}.dirty"),
        ("{tag}.post{ccount}+dirty", "1.0.0.post{ccount}+dirty"),
        ("{tag}+dirty", "1.0.0+dirty"),
    ],
)
@pytest.mark.parametrize("add", [True, False])
def test_version_file_dirty(repo, create_config, add, template, subst):
    config = {
        "version_file": "VERSION.txt",
        "count_commits_from_version_file": True,
    }
    if template:
        # template is not ignored
        config["dirty_template"] = template

    create_config(repo, config)

    create_file(repo, "VERSION.txt", "1.0.0")
    create_file(repo, commit=False)

    full_sha = get_full_sha(repo)
    sha = get_sha(repo)
    assert get_version(repo) == subst.format(sha=sha, full_sha=full_sha, ccount=0)

    create_commit(repo, "add file")
    create_file(repo, add=False)

    full_sha = get_full_sha(repo)
    sha = get_sha(repo)
    assert get_version(repo) == subst.format(sha=sha, full_sha=full_sha, ccount=1)


@pytest.mark.parametrize(
    "version, real_version",
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
@pytest.mark.parametrize("count_commits_from_version_file", [True, False])
def test_version_file_sanitization(repo, create_config, version, real_version, count_commits_from_version_file):
    create_config(
        repo,
        {
            "version_file": "VERSION.txt",
            "dev_template": "{tag}",
            "count_commits_from_version_file": count_commits_from_version_file,
        },
    )
    create_file(repo, "VERSION.txt", version)

    assert get_version(repo) == real_version


@pytest.mark.parametrize(
    "version",
    [
        "alpha1.0.0",
        "1.0.0abc",
        "1.0.0.abc",
        "1.0.0-abc",
        "1.0.0_abc",
    ],
)
@pytest.mark.parametrize("count_commits_from_version_file", [True, False])
def test_version_file_wrong_version_number(repo, version, create_config, count_commits_from_version_file):
    create_config(
        repo,
        {
            "version_file": "VERSION.txt",
            "dev_template": "{tag}",
            "count_commits_from_version_file": count_commits_from_version_file,
        },
    )
    create_file(repo, "VERSION.txt", version)

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)


@pytest.mark.flaky(reruns=3)  # sha and full_sha can start with 0 which are removed, just try again
def test_version_file_tagged_history(repo, create_config):
    create_tag(repo, "1.2.3")

    create_file(repo, "VERSION.txt", "1.0.0")
    create_config(
        repo,
        {
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
        },
    )

    sha = get_sha(repo)
    assert get_version(repo) == f"1.0.0.post1+git.{sha}"


@pytest.mark.flaky(reruns=3)  # sha and full_sha can start with 0 which are removed, just try again
def test_version_file_tagged_head(repo, create_config):
    create_file(repo, "VERSION.txt", "1.0.0")
    create_config(
        repo,
        {
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
        },
    )
    create_tag(repo, "1.2.3")

    # template is for release, because commit is tagged
    # but version_file content is up to user
    assert get_version(repo) == "1.0.0"


@pytest.mark.parametrize("starting_version, version", [(None, "0.0.1"), ("1.2.3", "1.2.3")])
@pytest.mark.parametrize("create_version", [True, False])
def test_version_file_missing(repo, create_config, create_version, starting_version, version):
    config = {
        "version_file": "VERSION.txt",
        "count_commits_from_version_file": True,
    }
    if starting_version:
        config["starting_version"] = starting_version
    if create_version:
        create_file(repo, "VERSION.txt", "")

    create_config(repo, config)

    assert get_version(repo) == version


@pytest.mark.parametrize("count_commits", [True, False])
def test_version_file_not_a_repo(repo_dir, create_config, count_commits):
    create_file(
        repo_dir,
        "VERSION.txt",
        "1.0.0",
        add=False,
        commit=False,
    )
    create_config(
        repo_dir,
        {
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": count_commits,
        },
        add=False,
        commit=False,
    )

    assert get_version(repo_dir) == "1.0.0"
