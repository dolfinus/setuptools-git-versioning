import os
import subprocess
import textwrap
import time
from datetime import datetime, timedelta

import pytest

from tests.lib.util import (
    create_commit,
    create_file,
    create_tag,
    get_sha,
    get_version,
    get_version_module,
    get_version_script,
)

pytestmark = pytest.mark.all


@pytest.mark.important
@pytest.mark.parametrize(
    "tag_filter, version",
    [
        ("product_x/(?P<tag>.*)", "1.1.0"),
        ("product_y/(?P<tag>.*)", "1.1.10"),
        ("product_z/foo/(?P<tag>.*)", "1.1.1"),
    ],
)
def test_tag_filter(repo, create_config, tag_filter, version):
    if tag_filter:
        create_config(repo, {"tag_filter": tag_filter, "tag_formatter": tag_filter})
    else:
        create_config(repo)

    commits = {}
    tags_to_commit = [
        "product_x/1.0.0",
        "product_x/1.0.2",
        "product_x/1.1.0",
        "product_y/1.1.10",
        "product_z/foo/1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=len(tags_to_commit) - i)
        create_commit(repo, "Some commit", dt=dt)
        commits[tag] = get_sha(repo)
        time.sleep(1)

    tags_to_create = [
        "product_x/1.0.0",
        "product_x/1.0.2",
        "product_x/1.1.0",
        "product_y/1.1.10",
        "product_z/foo/1.1.1",
    ]

    for tag in tags_to_create:
        create_tag(repo, tag, message="", commit=commits[tag])
        time.sleep(1)

    assert get_version(repo).startswith(version)


@pytest.mark.parametrize(
    "tag, version, filter_regex, tag_format",
    [
        ("1.0.0", "1.0.0", r"[\d.]+", None),
        ("release/1.0.0", "0.0.1", r"[\d.]+", None),
        ("unknown", "0.0.1", r"[\d.]+", None),
        ("foo/bar/1.0.3-123", "1.0.3.123", r"foo/bar/.*", r"foo/bar/(?P<tag>.*)"),
    ],
)
def test_tag_filter_external(repo, create_config, tag, version, filter_regex, tag_format):
    create_file(
        repo,
        "util.py",
        textwrap.dedent(
            rf"""
            import re

            def tag_filter(tag: str) -> str:
                if re.match(r"{filter_regex}", tag):
                    return tag
                return None
            """
        ),
    )

    create_config(
        repo,
        {
            "tag_filter": "util:tag_filter",
            "tag_formatter": tag_format,
        },
    )
    create_tag(repo, tag)

    assert get_version(repo) == version
    assert get_version_script(repo) == version
    assert get_version_module(repo) == version

    # path to the repo can be passed as positional argument
    assert get_version_script(os.getcwd(), args=[repo]) == version
    assert get_version_module(os.getcwd(), args=[repo]) == version


@pytest.mark.parametrize(
    "tag, filter_regex",
    [
        ("foo/bar/1.2.0", r"foo/bar/.*"),
    ],
)
def test_tag_filter_missing_format(repo, create_config, tag, filter_regex):
    create_file(
        repo,
        "util.py",
        textwrap.dedent(
            rf"""
            import re

            def tag_filter(tag: str) -> str:
                if re.match(r"{filter_regex}", tag):
                    return tag
                return None
            """
        ),
    )

    create_config(
        repo,
        {
            "tag_filter": "util:tag_filter",
        },
    )
    create_tag(repo, tag)

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)
