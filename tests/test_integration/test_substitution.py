import re
import subprocess
from datetime import datetime, timezone

import pytest

from setuptools_git_versioning import subst
from tests.lib.util import (
    checkout_branch,
    create_file,
    create_setup_py,
    create_tag,
    get_version_setup_py,
)

pytestmark = pytest.mark.all


@pytest.mark.parametrize(
    "template",
    [
        "{tag}",
        "{tag}+a{tag}",
    ],
)
def test_substitution_tag(repo, template):
    create_setup_py(repo, {"template": template})
    create_tag(repo, "1.2.3")

    assert get_version_setup_py(repo) == template.format(tag="1.2.3")


@pytest.mark.parametrize(
    "dev_template",
    [
        "{tag}.{ccount}",
        "{tag}.{ccount}+a{ccount}",
    ],
)
def test_substitution_ccount(repo, dev_template):
    create_setup_py(repo, {"dev_template": dev_template})
    create_tag(repo, "1.2.3")
    create_file(repo)

    assert get_version_setup_py(repo) == dev_template.format(tag="1.2.3", ccount=1)


@pytest.mark.parametrize(
    ("branch", "suffix"),
    [
        ("alpha", "a"),
        ("beta", "b"),
        ("dev", ".dev"),
        ("pre", "rc"),
        ("preview", "rc"),
        ("post", ".post"),
    ],
)
@pytest.mark.parametrize(
    ("template", "real_template"),
    [
        ("{tag}{branch}", "{tag}{suffix}0"),
        ("{tag}{branch}+a{branch}", "{tag}{suffix}0+a{branch}"),
    ],
)
def test_substitution_branch(repo, template, real_template, branch, suffix):
    checkout_branch(repo, branch)
    create_setup_py(repo, {"template": template})
    create_tag(repo, "1.2.3")

    assert get_version_setup_py(repo) == real_template.format(tag="1.2.3", branch=branch, suffix=suffix)


@pytest.mark.parametrize(
    ("dev_template", "pipeline_id", "suffix"),
    [
        # leading zeros are removed by setuptools
        ("{tag}.post{env:PIPELINE_ID}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID}", "0234", "234"),
        ("{tag}.post{env:PIPELINE_ID:123}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:123}", None, "123"),
        ("{tag}.post{env:PIPELINE_ID:IGNORE}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:IGNORE}", None, "0"),
        ("{tag}.post{env:PIPELINE_ID:}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{ccount}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{ccount}}", None, "1"),
        ("{tag}.post{env:PIPELINE_ID:{timestamp:%Y}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{timestamp:%Y}}", None, datetime.now().year),
        ("{tag}.post{env:PIPELINE_ID:{env:ANOTHER_ENV}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{env:ANOTHER_ENV}}", None, "345"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV:IGNORE}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV:IGNORE}}", None, "0"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV:}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV:567}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV:567}}", None, "567"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV:{ccount}}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV:{ccount}}}", None, "1"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV:{timestamp:%Y}}}", "234", "234"),
        ("{tag}.post{env:PIPELINE_ID:{env:MISSING_ENV:{timestamp:%Y}}}", None, datetime.now().year),
        ("{tag}.post{env:PIPELINE_ID}+abc{env:ANOTHER_ENV}", "234", "234+abc345"),
        ("{tag}.post{env:PIPELINE_ID}+abc{env:MISSING_ENV}", "234", "234+abcunknown"),
        ("{tag}.post{env:PIPELINE_ID}+abc{env:MISSING_ENV:5.6.7}", "234", "234+abc5.6.7"),
        ("{tag}.post{env:PIPELINE_ID}+abc{env:MISSING_ENV:B-C-D}", "234", "234+abcb.c.d"),
        ("{tag}.post{env:PIPELINE_ID}+abc{env:MISSING_ENV:IGNORE}d", "234", "234+abcd"),
        ("{tag}.post{env:PIPELINE_ID}+abc{env:MISSING_ENV:}d", "234", "234+abcunknownd"),
        ("{tag}.post{env:PIPELINE_ID}+abc{env:MISSING_ENV:.}d", "234", "234+abc.d"),
        ("{tag}.post{env:PIPELINE_ID}+abc{env:MISSING_ENV:{ccount}}", "234", "234+abc1"),
        (
            "{tag}.post{env:PIPELINE_ID}+abc{env:MISSING_ENV:{timestamp:%Y}}",
            "234",
            "234+abc" + str(datetime.now().year),
        ),
        # empty env variable name
        ("{tag}.post{env:PIPELINE_ID}+abc{env: }d", "234", "234+abcunknownd"),
    ],
)
def test_substitution_env(repo, dev_template, pipeline_id, suffix):
    create_setup_py(repo, {"dev_template": dev_template})
    create_tag(repo, "1.2.3")
    create_file(repo)

    env = {"ANOTHER_ENV": "345"}
    if pipeline_id is not None:
        env["PIPELINE_ID"] = pipeline_id

    assert get_version_setup_py(repo, env=env) == f"1.2.3.post{suffix}"


@pytest.mark.flaky(reruns=3)  # running subprocess takes some time, so we can get previous second
@pytest.mark.important
@pytest.mark.parametrize(
    ("template", "fmt", "callback"),
    [
        ("{tag}.post{timestamp}", "{tag}.post{}", lambda dt: (int(dt.timestamp()) // 100,)),
        ("{tag}.post{timestamp:}", "{tag}.post{}", lambda dt: (int(dt.timestamp()) // 100,)),
        ("{tag}.post{timestamp:%s}", "{tag}.post{}", lambda dt: (int(dt.timestamp()) // 100,)),
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
        # pure string
        ("{tag}+git.{timestamp:abc}", "{tag}+git.abc", lambda x: []),
    ],
)
def test_substitution_timestamp(repo, template, fmt, callback):
    create_setup_py(repo, {"template": template})
    create_tag(repo, "1.2.3")

    value = fmt.format(*callback(datetime.now()), tag="1.2.3", ccount=0)
    pattern = re.compile(r"([^\d\w])0+(\d+[^\d\w]|\d+$)")
    while True:
        # leading zeros are removed even in local part of version
        new_value = pattern.sub(r"\1\2", value)
        if new_value == value:
            break
        value = new_value

    assert new_value in get_version_setup_py(repo)


class DatetimeWithoutUnixFormat(datetime):
    """Fixed current time, and strftime rejects ``%s`` like on Windows."""

    @classmethod
    def now(cls, tz=None):
        return cls(2024, 1, 15, 12, 34, 56, tzinfo=timezone.utc)

    def astimezone(self, tz=None):
        return self

    def strftime(self, fmt):
        if "%s" in fmt:
            msg = "Invalid format string"
            raise ValueError(msg)
        return super().strftime(fmt)


@pytest.mark.parametrize(
    ("template", "result"),
    [
        ("{timestamp}", "1705322096"),
        ("{timestamp:}", "1705322096"),
        ("{timestamp:%s}", "1705322096"),
        ("{tag}.post{timestamp}", "{tag}.post1705322096"),
        ("{timestamp:%Y}.{timestamp:%m}", "2024.01"),
    ],
)
def test_substitution_timestamp_without_strftime_unix_format(monkeypatch, template, result):
    monkeypatch.setattr(subst, "datetime", DatetimeWithoutUnixFormat)

    assert subst.substitute_timestamp(template) == result


@pytest.mark.parametrize(
    "template",
    [
        "{tag}+a{env}",
        "{tag}+a{env:}",
        "{tag}.post{env:{}}",
        "{tag}+a{env:MISSING_ENV:{}",
        "{tag}+a{env:MISSING_ENV:{{}}",
        "{tag}+a{env:MISSING_ENV:}}",
        "{tag}+a{env:MISSING_ENV:{}}}",
        "{tag}+a{timestamp:A:B}",
        "{tag}+a{timestamp:{%Y}",
    ],
)
def test_substitution_wrong_format(repo, template):
    create_setup_py(repo, {"template": template})
    create_tag(repo, "1.2.3")

    with pytest.raises(subprocess.CalledProcessError):
        get_version_setup_py(repo)
