import os
import subprocess
import textwrap
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
    create_config(repo, {"tag_filter": tag_filter, "tag_formatter": tag_filter})

    tags_to_commit = [
        "product_x/1.0.0",
        "product_x/1.0.2",
        "product_x/1.1.0",
        "product_y/1.1.10",
        "product_z/foo/1.1.1",
    ]

    for i, tag in enumerate(tags_to_commit):
        create_file(repo, commit=False)
        dt = datetime.now() - timedelta(days=10) + timedelta(days=i)
        create_commit(repo, "Some commit", dt=dt)
        create_tag(repo, tag, message="", commit=get_sha(repo))

    assert get_version(repo).startswith(version)


@pytest.mark.parametrize(
    "tag, version, filter_regex",
    [
        ("1.0.0", "1.0.0", r"(?P<tag>[\d.]+)"),
        ("release/1.0.0", "0.0.1", r"(?P<tag>[\d.]+)"),
        ("unknown", "0.0.1", r"(?P<tag>[\d.]+)"),
        ("foo/bar/1.0.3-123", "1.0.3.123", r"foo/bar/(?P<tag>.*)"),
    ],
)
def test_tag_filter_external(repo, create_config, tag, version, filter_regex):
    create_file(
        repo,
        "util.py",
        textwrap.dedent(
            rf"""
            from __future__ import annotations # For `str | None` type syntax

            import re

            def tag_filter(tag: str) -> str | None:
                m = re.match(r"{filter_regex}", tag)

                if m:
                    return m.group('tag')
                return None
            """
        ),
    )

    create_config(
        repo,
        {
            "tag_filter": "util:tag_filter",
            "tag_formatter": "util:tag_filter",
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


def test_tag_filter_invalid_regex(repo, create_config):
    create_config(
        repo,
        {"tag_filter": "abc(.*"},
    )
    create_tag(repo, "1.0.0")

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)
