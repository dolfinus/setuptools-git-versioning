import pytest
import textwrap

from tests.conftest import execute, create_file, get_version


VERSION_PY_CALLABLE_GENERIC = textwrap.dedent(
    """
    def get_version():
        return "{version}"

    def get_template_name():
        return "{template_name}"

    def get_template():
        return "{template}"
"""
)
VERSION_PY_CALLABLE = VERSION_PY_CALLABLE_GENERIC.format(version="{version}", template_name="", template="")

VERSION_PY_STR_GENERIC = textwrap.dedent(
    """
    __version__ = "{version}"
    __template_name__ = "{template_name}"
    __template__ = "{template}"
"""
)
VERSION_PY_STR = VERSION_PY_STR_GENERIC.format(version="{version}", template_name="", template="")

SETUP_PY_CALLABLE = textwrap.dedent(
    """
    import setuptools
    from version import get_version, get_template_name, get_template

    setuptools.setup(
        version_config={
            "version_callback": get_version,
            get_template_name(): get_template()
        },
        setup_requires=["setuptools-git-versioning"]
    )
"""
)

SETUP_PY_STR = textwrap.dedent(
    """
    import setuptools

    from version import __version__, __template_name__, __template__

    setuptools.setup(
        version_config={
            "version_callback": __version__,
            __template_name__: __template__
        },
        setup_requires=["setuptools-git-versioning"]
    )
"""
)


@pytest.mark.parametrize(
    "version_py, setup_py",
    [
        (VERSION_PY_CALLABLE, SETUP_PY_CALLABLE),
        (VERSION_PY_STR, SETUP_PY_STR),
    ],
    ids=["callable input", "str input"],
)
def test_version_callback(repo, version_py, setup_py):
    create_file(repo, "version.py", version_py.format(version="1.0.0"), commit=False)
    create_file(
        repo,
        "setup.py",
        setup_py,
    )

    assert get_version(repo) == "1.0.0"

    create_file(repo)
    assert get_version(repo) == "1.0.0"


@pytest.mark.parametrize(
    "version_py, setup_py",
    [
        (VERSION_PY_CALLABLE, SETUP_PY_CALLABLE),
        (VERSION_PY_STR, SETUP_PY_STR),
    ],
    ids=["callable input", "str input"],
)
@pytest.mark.parametrize(
    "version, real_version",
    [
        ("1.0.0", "1.0.0"),
        ("v1.2.3", "1.2.3"),
        ("abc1.2.3", "abc1.2.3"),
    ],
)
def test_version_callback_drop_leading_v(repo, version, real_version, version_py, setup_py):
    create_file(repo, "version.py", version_py.format(version=version), commit=False)
    create_file(
        repo,
        "setup.py",
        setup_py,
    )
    assert get_version(repo) == real_version


@pytest.mark.parametrize(
    "version_py, setup_py",
    [
        (VERSION_PY_CALLABLE, SETUP_PY_CALLABLE),
        (VERSION_PY_STR, SETUP_PY_STR),
    ],
    ids=["callable input", "str input"],
)
def test_version_callback_not_a_repo(repo_dir, version_py, setup_py):
    version = "1.0.0"
    create_file(repo_dir, "version.py", version_py.format(version=version), add=False, commit=False)
    create_file(
        repo_dir,
        "setup.py",
        setup_py,
        add=False,
        commit=False,
    )

    assert get_version(repo_dir) == version


@pytest.mark.parametrize(
    "version_py, setup_py",
    [
        (VERSION_PY_CALLABLE, SETUP_PY_CALLABLE),
        (VERSION_PY_STR, SETUP_PY_STR),
    ],
    ids=["callable input", "str input"],
)
def test_version_callback_tag_is_preferred(repo, version_py, setup_py):
    create_file(repo, "version.py", version_py.format(version="1.0.0"), commit=False)
    create_file(
        repo,
        "setup.py",
        setup_py,
    )

    execute(repo, "git tag 1.2.3")
    assert get_version(repo) == "1.2.3"


@pytest.mark.parametrize(
    "version_py, setup_py",
    [
        (VERSION_PY_CALLABLE, SETUP_PY_CALLABLE),
        (VERSION_PY_STR, SETUP_PY_STR),
    ],
    ids=["callable input", "str input"],
)
def test_version_callback_has_more_priority_than_version_file(repo, version_py, setup_py):
    create_file(repo, "VERSION.txt", "1.2.3")
    version = "1.0.0"

    create_file(repo, "version.py", version_py.format(version=version), commit=False)
    create_file(
        repo,
        "setup.py",
        setup_py,
    )

    assert get_version(repo) == version


@pytest.mark.parametrize(
    "version_py, setup_py",
    [
        (VERSION_PY_CALLABLE_GENERIC, SETUP_PY_CALLABLE),
        (VERSION_PY_STR_GENERIC, SETUP_PY_STR),
    ],
    ids=["callable input", "str input"],
)
@pytest.mark.parametrize(
    "template",
    [
        "{tag}.post{env:PIPELINE_ID:123}",
        "{tag}.post{env:PIPELINE_ID:123}",
        "{tag}.post{env:PIPELINE_ID:IGNORE}",
        "{tag}.post{env:PIPELINE_ID:IGNORE}",
        "{tag}.post{env:PIPELINE_ID:{ccount}}",
        "{tag}.post{env:PIPELINE_ID:{ccount}}",
        "{tag}.post{timestamp}",
        "{tag}.post{timestamp:%s}",
        "{timestamp:%Y}.{timestamp:%m}.{timestamp:%d}+{timestamp:%H%M%S}",
        "{tag}.post{ccount}+{timestamp:%Y-%m-%dT%H-%M-%S}",
        "{tag}.post{ccount}+git.{full_sha}",
        "{tag}.post{ccount}+git.{sha}",
        "{tag}.post{ccount}",
        "{tag}.{branch}{ccount}",
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
def test_version_callback_template_substitutions_are_ignored(
    repo,
    state,
    template_name,
    template,
    version_py,
    setup_py,
):
    version = "1.0.0"

    create_file(
        repo,
        "version.py",
        version_py.format(version=version, template_name=template_name, template=template),
        commit=False,
    )
    create_file(
        repo,
        "setup.py",
        setup_py,
    )

    if state == "tag":
        ccount = 0
    else:
        ccount = 5

    for _ in range(ccount):
        create_file(repo)

    if state == "dirty":
        create_file(repo, commit=False)

    assert get_version(repo) == version
