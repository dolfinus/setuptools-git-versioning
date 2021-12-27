from datetime import datetime, timedelta
import pytest
import re
import textwrap
import time

from tests.conftest import execute, create_file, create_setup_py, get_commit, get_version, get_short_commit


def test_tag(repo):
    create_setup_py(repo)

    execute(repo, "git tag 1.0.0")
    assert get_version(repo) == "1.0.0"


@pytest.mark.parametrize(
    "tag, version",
    [
        ("1.0.0", "1.0.0"),
        ("v1.2.3", "1.2.3"),
        ("abc1.2.3", "abc1.2.3"),
    ],
)
def test_tag_drop_leading_v(repo, tag, version):
    create_setup_py(repo)

    execute(repo, "git tag {tag}".format(tag=tag))
    assert get_version(repo) == version


def test_tag_missing(repo):
    create_setup_py(repo)
    assert get_version(repo) == "0.0.1"


def test_tag_not_a_repo(repo_dir):
    create_setup_py(repo_dir, add=False, commit=False)

    assert get_version(repo_dir) == "0.0.1"


def test_tag_non_linear_history(repo):
    execute(repo, "git checkout -b dev")
    create_file(repo, commit=False)
    create_setup_py(repo)

    execute(repo, "git checkout master")
    create_file(repo, commit=False)
    create_setup_py(repo)
    execute(repo, "git tag 1.0.0")

    execute(repo, "git checkout dev")
    create_file(repo)
    assert get_version(repo) == "0.0.1"


def test_tag_linear_history(repo):
    execute(repo, "git tag 1.0.0")
    execute(repo, "git checkout -b dev")
    create_setup_py(repo)

    sha = get_short_commit(repo)
    assert get_version(repo) == "1.0.0.post1+git.{sha}".format(sha=sha)


@pytest.mark.parametrize(
    "starting_version",
    [
        "1.0.0",
        "1.2.3",
    ],
)
def test_tag_missing_with_starting_version(repo, starting_version):
    create_setup_py(repo, {"starting_version": starting_version})

    assert get_version(repo) == starting_version


def test_tag_dev(repo):
    execute(repo, "git tag 1.0.0")
    create_setup_py(repo)

    sha = get_short_commit(repo)
    assert get_version(repo) == "1.0.0.post1+git.{sha}".format(sha=sha)


@pytest.mark.parametrize("add", [True, False])
def test_tag_dirty(repo, add):
    create_setup_py(repo)
    execute(repo, "git tag 1.0.0")

    create_file(repo, add=add, commit=False)

    sha = get_short_commit(repo)
    assert get_version(repo) == "1.0.0.post0+git.{sha}.dirty".format(sha=sha)


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
        ("tag", "template"),
        ("dev", "dev_template"),
        ("dirty", "dirty_template"),
    ],
)
def test_tag_template_substitutions(repo, state, template_name, template):
    tag = "1.0.0"

    create_setup_py(repo, {template_name: template})
    execute(repo, "git tag {tag}".format(tag=tag))

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

    assert get_version(repo) == template.format(tag=tag, ccount=ccount, sha=sha, full_sha=full_sha)


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
        ("tag", "template"),
        ("dev", "dev_template"),
        ("dirty", "dirty_template"),
    ],
)
def test_tag_template_substitution_branch(repo, state, template_name, branch, suffix, branch_formatter):
    execute(repo, "git checkout -b {branch}".format(branch=branch))

    tag = "1.0.0"

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

    execute(repo, "git tag {tag}".format(tag=tag))

    if state == "tag":
        ccount = 0
    else:
        ccount = 5

        for _ in range(ccount):
            create_file(repo)

    if state == "dirty":
        create_file(repo, commit=False)

    assert get_version(repo) == "{tag}{suffix}{ccount}".format(tag=tag, suffix=suffix, ccount=ccount)


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
        ("tag", "template"),
        ("dev", "dev_template"),
        ("dirty", "dirty_template"),
    ],
)
def test_tag_template_substitution_env(repo, state, template_name, template, pipeline_id, real_pipeline_id):
    tag = "1.0.0"

    create_setup_py(repo, {template_name: template})
    execute(repo, "git tag {tag}".format(tag=tag))

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
    assert get_version(repo, env=env) == "{tag}.post{suffix}".format(tag=tag, suffix=suffix)


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
        ("tag", "template"),
        ("dev", "dev_template"),
        ("dirty", "dirty_template"),
    ],
)
def test_tag_template_substitution_timestamp(repo, state, template_name, template, fmt, callback):
    tag = "1.0.0"
    create_setup_py(repo, {template_name: template})
    execute(repo, "git tag {tag}".format(tag=tag))

    if state == "tag":
        ccount = 0
    else:
        ccount = 5

        for _ in range(ccount):
            create_file(repo)

    if state == "dirty":
        create_file(repo, commit=False)

    value = fmt.format(tag=tag, ccount=ccount, *callback(datetime.now()))
    value = re.sub("([^\\d\\w])0+(\\d)", r"\1\2", value)  # leading zeros are removed even in local part of version
    assert value in get_version(repo)


@pytest.mark.parametrize("tag_opts", ["", "-a -m 'Some message'"])
def test_tag_sort_by_version(repo, tag_opts):
    sort_by = "version:refname"
    create_setup_py(repo, {"sort_by": sort_by})

    commits = {}

    tags_to_commit = [
        "1.1.0",
        "1.1.10",
        "1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=len(tags_to_commit) - i)
        execute(repo, "git commit -m 'Some commit' --date {dt}".format(dt=dt.isoformat()))
        commits[tag] = get_short_commit(repo)

    tags_to_create = [
        "1.1.0",
        "1.1.10",
        "1.1.1",
    ]

    for tag in tags_to_create:
        execute(repo, "git tag {tag_opts} {tag} {commit}".format(tag=tag, tag_opts=tag_opts, commit=commits[tag]))

    # the result is not stable because latest tag (by name)
    # has nothing in common with commit creation time
    # so it could mess everything up: https://github.com/dolfinus/setuptools-git-versioning/issues/22
    # that's why this value is not default
    assert "1.1.10" in get_version(repo)


@pytest.mark.parametrize("tag_opts", ["", "-a -m 'Some message'"])
def test_tag_sort_by_commit_date(repo, tag_opts):
    sort_by = "committerdate"
    create_setup_py(repo, {"sort_by": sort_by})

    commits = {}
    tags_to_commit = [
        "1.1.10",
        "1.1.0",
        "1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=len(tags_to_commit) - i)
        execute(repo, "git commit -m 'Some commit' --date {dt}".format(dt=dt.isoformat()))
        commits[tag] = get_short_commit(repo)
        time.sleep(1)

    tags_to_create = [
        "1.1.0",
        "1.1.1",
        "1.1.10",
    ]

    for tag in tags_to_create:
        execute(repo, "git tag {tag_opts} {tag} {commit}".format(tag=tag, tag_opts=tag_opts, commit=commits[tag]))

    if not tag_opts:
        assert get_version(repo) == "1.1.1"
    else:
        assert get_version(repo).startswith("1.1")
        # the result is totally random because annotaged tags have no such field at all
        # https://github.com/dolfinus/setuptools-git-versioning/issues/23


@pytest.mark.parametrize("tag_opts", ["", "-a -m 'Some message'"])
def test_tag_sort_by_tag_date(repo, tag_opts):
    sort_by = "taggerdate"
    create_setup_py(repo, {"sort_by": sort_by})

    commits = {}
    tags_to_commit = [
        "1.1.10",
        "1.1.0",
        "1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=len(tags_to_commit) - i)
        execute(repo, "git commit -m 'Some commit' --date {dt}".format(dt=dt.isoformat()))
        commits[tag] = get_short_commit(repo)

    tags_to_create = [
        "1.1.0",
        "1.1.1",
        "1.1.10",
    ]

    for tag in tags_to_create:
        execute(repo, "git tag {tag_opts} {tag} {commit}".format(tag=tag, tag_opts=tag_opts, commit=commits[tag]))
        time.sleep(1)

    if tag_opts:
        # the result is not stable because latest tag (by creation time)
        # has nothing in common with commit creation time
        assert "1.1.10" in get_version(repo)
    else:
        assert get_version(repo).startswith("1.1")
        # the result is totally random because annotaged tags have no such field at all
        # https://github.com/dolfinus/setuptools-git-versioning/issues/23


@pytest.mark.parametrize("sort_by", [None, "creatordate"])
@pytest.mark.parametrize("tag_opts", ["", "-a -m 'Some message'"])
def test_tag_sort_by_create_date(repo, tag_opts, sort_by):
    if sort_by:
        create_setup_py(repo, {"sort_by": sort_by})
    else:
        create_setup_py(repo)

    commits = {}
    tags_to_commit = [
        "1.1.0",
        "1.1.10",
        "1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=len(tags_to_commit) - i)
        execute(repo, "git commit -m 'Some commit' --date {dt}".format(dt=dt.isoformat()))
        commits[tag] = get_short_commit(repo)
        time.sleep(1)

    tags_to_create = [
        "1.1.10",
        "1.1.1",
        "1.1.0",
    ]

    for tag in tags_to_create:
        execute(repo, "git tag {tag_opts} {tag} {commit}".format(tag=tag, tag_opts=tag_opts, commit=commits[tag]))
        time.sleep(1)

    if tag_opts:
        # the result is not stable because latest tag (by creation time)
        # has nothing in common with commit creation time
        # so it is not recommended to create annotated tags in the past
        assert "1.1.0" in get_version(repo)
    else:
        # but at least creatordate field is present in both tag types
        # https://stackoverflow.com/questions/67206124
        # so this is a default value
        assert get_version(repo) == "1.1.1"
