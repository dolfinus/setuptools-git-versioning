from datetime import datetime
import textwrap
import pytest
import re

from tests.conftest import execute, create_file, create_setup_py, get_commit, get_version, get_short_commit


def test_version_file(repo):
    create_setup_py(
        repo,
        {
            "version_file": "VERSION.txt",
        },
    )

    create_file(repo, "VERSION.txt", "1.0.0")
    assert get_version(repo) == "1.0.0"

    create_file(repo)
    assert get_version(repo) == "1.0.0"


def test_version_file_count_commits(repo):
    create_setup_py(
        repo,
        {
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
            # "template" is used only in case of tag build, which is not the case
        },
    )

    create_file(repo, "VERSION.txt", "1.0.0")

    sha = get_short_commit(repo)
    assert get_version(repo) == "1.0.0.post0+git.{sha}".format(sha=sha)

    create_file(repo)

    sha = get_short_commit(repo)
    assert get_version(repo) == "1.0.0.post1+git.{sha}".format(sha=sha)


@pytest.mark.parametrize(
    "version, real_version",
    [
        ("1.0.0", "1.0.0"),
        ("v1.2.3", "1.2.3"),
        ("abc1.2.3", "abc1.2.3"),
    ],
)
def test_version_file_drop_leading_v(repo, version, real_version):
    create_file(repo, "VERSION.txt", version)
    create_setup_py(
        repo,
        {
            "version_file": "VERSION.txt",
        },
    )

    assert get_version(repo) == real_version


def test_version_file_tag_is_preferred(repo):
    execute(repo, "git tag 1.2.3")

    create_file(repo, "VERSION.txt", "1.0.0")
    create_setup_py(
        repo,
        {
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
        },
    )

    sha = get_short_commit(repo)
    assert get_version(repo) == "1.2.3.post2+git.{sha}".format(sha=sha)


def test_version_file_missing(repo):
    create_setup_py(
        repo,
        {
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
        },
    )

    assert get_version(repo) == "0.0.1"


def test_version_file_not_a_repo(repo_dir):
    create_file(
        repo_dir,
        "VERSION.txt",
        "1.0.0",
        add=False,
        commit=False,
    )
    create_setup_py(
        repo_dir,
        {
            "version_file": "VERSION.txt",
        },
        add=False,
        commit=False,
    )

    assert get_version(repo_dir) == "1.0.0"


def test_version_file_not_a_repo_count_commits(repo_dir):
    create_file(
        repo_dir,
        "VERSION.txt",
        "1.0.0",
        add=False,
        commit=False,
    )
    create_setup_py(
        repo_dir,
        {
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
        },
        add=False,
        commit=False,
    )

    assert get_version(repo_dir) == "1.0.0"


def test_version_file_dev(repo):
    create_file(repo, "VERSION.txt", "1.0.0")

    create_setup_py(
        repo,
        {
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
            "dev_template": "{tag}.dev{ccount}+git.{sha}",
        },
    )

    sha = get_short_commit(repo)
    assert get_version(repo) == "1.0.0.dev1+git.{sha}".format(sha=sha)


@pytest.mark.parametrize("add", [True, False])
def test_version_file_dirty(repo, add):
    create_file(repo, "VERSION.txt", "1.0.0")

    create_setup_py(
        repo,
        {
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
            "dirty_template": "{tag}.dev{ccount}+git.{sha}.dirty",
        },
    )

    create_file(repo, add=add, commit=False)

    sha = get_short_commit(repo)
    assert get_version(repo) == "1.0.0.dev1+git.{sha}.dirty".format(sha=sha)


@pytest.mark.parametrize(
    "template",
    [
        "{tag}.post{ccount}+git.{full_sha}",
        "{tag}.post{ccount}+git.{sha}",
        "{tag}.post{ccount}",
        "{tag}",
    ],
)
@pytest.mark.parametrize(
    "state, template_name",
    [
        ("tag", "dev_template"),
        ("dev", "dev_template"),
        ("dirty", "dirty_template"),
    ],
)
def test_version_file_template_substitutions(repo, state, template_name, template):
    version = "1.0.0"
    create_setup_py(
        repo,
        {
            template_name: template,
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
        },
    )
    create_file(repo, "VERSION.txt", version)

    if state == "tag":
        ccount = 0
    else:
        ccount = 5

    for _ in range(ccount):
        create_file(repo)

    full_sha = get_commit(repo)
    sha = get_short_commit(repo)

    if state == "dirty":
        create_file(repo, commit=False)

    assert get_version(repo) == template.format(tag=version, ccount=ccount, sha=sha, full_sha=full_sha)


@pytest.mark.parametrize(
    "branch, suffix, branch_formatter",
    [
        ("alpha", "a", None),
        ("beta", "b", None),
        ("dev", ".dev", None),
        ("pre", "rc", None),
        ("preview", "rc", None),
        ("post", ".post", None),
        ("feature/issue-1234-add-a-great-feature", ".1234", 'lambda branch: re.sub("[^\\d]+", "", branch)'),
    ],
)
@pytest.mark.parametrize(
    "state, template_name",
    [
        ("tag", "dev_template"),
        ("dev", "dev_template"),
        ("dirty", "dirty_template"),
    ],
)
def test_version_file_template_substitution_branch(repo, state, template_name, branch, suffix, branch_formatter):
    execute(repo, "git checkout -b {branch}".format(branch=branch))

    version = "1.0.0"

    create_file(
        repo,
        "util.py",
        textwrap.dedent(
            """
            import re
            branch_formatter = {branch_formatter}
            template_name = '{template_name}'
        """.format(
                branch_formatter=branch_formatter or "''", template_name=template_name
            )
        ),
        commit=False,
    )

    create_file(
        repo,
        "setup.py",
        textwrap.dedent(
            """
            import setuptools
            from util import branch_formatter, template_name

            version_config = {
                template_name: "{tag}.{branch}{ccount}",
                "version_file": "VERSION.txt",
                "count_commits_from_version_file": True,
            }
            if branch_formatter:
                version_config["branch_formatter"] = branch_formatter

            setuptools.setup(
                version_config=version_config,
                setup_requires=["setuptools-git-versioning"]
            )
        """
        ),
    )

    create_file(repo, "VERSION.txt", version)

    if state == "tag":
        ccount = 0
    else:
        ccount = 5

        for _ in range(ccount):
            create_file(repo)

    if state == "dirty":
        create_file(repo, commit=False)

    assert get_version(repo) == "{tag}{suffix}{ccount}".format(tag=version, suffix=suffix, ccount=ccount)


@pytest.mark.parametrize(
    "template, pipeline_id, real_pipeline_id",
    [
        # leading zeros are removed by setuptools
        ("{tag}.post{env:PIPELINE_ID:123}", "0234", "234"),
        ("{tag}.post{env:PIPELINE_ID:123}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:123}", None, "123"),
        ("{tag}.post{env:PIPELINE_ID:IGNORE}", "0234", "234"),
        ("{tag}.post{env:PIPELINE_ID:IGNORE}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:IGNORE}", None, "0"),
        ("{tag}.post{env:PIPELINE_ID:{ccount}}", "0234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{ccount}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{ccount}}", None, "{ccount}"),
        ("{tag}.post{env:PIPELINE_ID}", "0234", "234"),
        ("{tag}.post{env:PIPELINE_ID}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID}", None, "UNKNOWN"),
    ],
)
@pytest.mark.parametrize(
    "state, template_name",
    [
        ("tag", "dev_template"),
        ("dev", "dev_template"),
        ("dirty", "dirty_template"),
    ],
)
def test_version_file_template_substitution_env(repo, state, template_name, template, pipeline_id, real_pipeline_id):
    version = "1.0.0"
    create_setup_py(
        repo,
        {
            template_name: template,
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
        },
    )
    create_file(repo, "VERSION.txt", version)

    if state == "tag":
        ccount = 0
    else:
        ccount = 5

        for _ in range(ccount):
            create_file(repo)

    if state == "dirty":
        create_file(repo, commit=False)

    env = {}
    if pipeline_id is not None:
        env = {"PIPELINE_ID": pipeline_id}

    suffix = real_pipeline_id.format(ccount=ccount)
    assert get_version(repo, env=env) == "{tag}.post{suffix}".format(tag=version, suffix=suffix)


@pytest.mark.parametrize(
    "template, fmt, callback",
    [
        ("{tag}.post{timestamp}", "{tag}.post{}", lambda dt: (int(dt.strftime("%s")) // 100,)),
        ("{tag}.post{timestamp:%s}", "{tag}.post{}", lambda dt: (int(dt.strftime("%s")) // 100,)),
        (
            "{timestamp:%Y}.{timestamp:%m}.{timestamp:%d}+{timestamp:%H%M%S}",
            "{}.{}.{}+{}",
            lambda dt: (dt.year, dt.month, dt.day, dt.strftime("%H%M")),
        ),
        (
            "{tag}.post{ccount}+{timestamp:%Y-%m-%dT%H-%M-%S}",
            "{tag}.post{ccount}+{}",
            lambda dt: (dt.strftime("%Y.%m.%dt%H.%M"),),
        ),
    ],
)
@pytest.mark.parametrize(
    "state, template_name",
    [
        ("tag", "dev_template"),
        ("dev", "dev_template"),
        ("dirty", "dirty_template"),
    ],
)
def test_version_file_template_substitution_timestamp(repo, state, template_name, template, fmt, callback):
    version = "1.0.0"
    create_setup_py(
        repo,
        {
            template_name: template,
            "version_file": "VERSION.txt",
            "count_commits_from_version_file": True,
        },
    )
    create_file(repo, "VERSION.txt", version)

    if state == "tag":
        ccount = 0
    else:
        ccount = 5

        for _ in range(ccount):
            create_file(repo)

    if state == "dirty":
        create_file(repo, commit=False)

    value = fmt.format(tag=version, ccount=ccount, *callback(datetime.now()))
    value = re.sub("([^\\d\\w])0+(\\d)", r"\1\2", value)  # leading zeros are removed even in local part of version
    assert value in get_version(repo)
