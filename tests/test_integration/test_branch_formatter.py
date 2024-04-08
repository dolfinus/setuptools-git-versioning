import os
import subprocess
import textwrap

import pytest

from tests.lib.util import (
    checkout_branch,
    create_file,
    get_version,
    get_version_module,
    get_version_script,
)

pytestmark = pytest.mark.all


@pytest.mark.parametrize(
    "branch, suffix",
    [
        ("1234", "1234"),
        ("feature/issue-1234-add-a-great-feature", "1234"),
        ("unknown", ""),
    ],
)
def test_branch_formatter_external(repo, template_config, create_config, branch, suffix):
    checkout_branch(repo, branch)

    create_file(
        repo,
        "util.py",
        textwrap.dedent(
            """
            import re

            def branch_formatter(branch):
                return re.sub("[^\\d]+", "", branch)
            """
        ),
    )

    template_config(
        repo,
        create_config,
        template="{tag}{branch}{ccount}",
        config={
            "branch_formatter": "util:branch_formatter",
        },
    )

    assert get_version(repo) == f"1.2.3{suffix}0"
    assert get_version_script(repo) == f"1.2.3{suffix}0"
    assert get_version_module(repo) == f"1.2.3{suffix}0"

    # path to the repo can be passed as positional argument
    assert get_version_script(os.getcwd(), args=[repo]) == f"1.2.3{suffix}0"
    assert get_version_module(os.getcwd(), args=[repo]) == f"1.2.3{suffix}0"


@pytest.mark.parametrize("create_util", [True, False])
def test_branch_formatter_external_missing(repo, template_config, create_config, create_util):
    if create_util:
        create_file(
            repo,
            "util.py",
            textwrap.dedent(
                """
                import re

                def branch_formatter(branch):
                    return re.sub("[^\\d]+", "", branch)
                """
            ),
        )

    template_config(
        repo,
        create_config,
        config={
            "branch_formatter": "util:wtf",
        },
    )

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)


def test_branch_formatter_external_not_callable(repo, template_config, create_config):
    create_file(
        repo,
        "util.py",
        textwrap.dedent(
            """
            import re

            branch_formatter = re.compile("[^\\d]+")
            """
        ),
    )

    template_config(
        repo,
        create_config,
        config={
            "branch_formatter": "util:branch_formatter",
        },
    )

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)


def test_branch_formatter_external_setup_py_direct_import(repo, template_config):
    branch = "feature/issue-1234-add-a-great-feature"
    suffix = ".1234"

    checkout_branch(repo, branch)

    def config_creator(root, cfg):
        return create_file(
            root,
            "setup.py",
            textwrap.dedent(
                f"""
                from coverage.control import Coverage

                coverage = Coverage()
                coverage.start()

                try:
                    import re
                    import setuptools
                    import pickle

                    def branch_formatter(branch):
                        return re.sub("[^\\d]+", "", branch)

                    version_config = {cfg}
                    version_config["branch_formatter"] = branch_formatter

                    setuptools.setup(
                        name="mypkg",
                        setuptools_git_versioning=version_config,
                        setup_requires=[
                            "setuptools>=41",
                            "wheel",
                            "setuptools-git-versioning",
                        ]
                    )
                finally:
                    coverage.stop()
                    coverage.save()
            """
            ),
        )

    template_config(repo, config_creator, template="{tag}.{branch}{ccount}")

    assert get_version(repo) == f"1.2.3{suffix}0"
    assert get_version_script(repo) == f"1.2.3{suffix}0"
    assert get_version_module(repo) == f"1.2.3{suffix}0"

    # path to the repo can be passed as positional argument
    assert get_version_script(os.getcwd(), args=[repo]) == f"1.2.3{suffix}0"
    assert get_version_module(os.getcwd(), args=[repo]) == f"1.2.3{suffix}0"


@pytest.mark.parametrize(
    "branch, suffix",
    [
        ("1234", "1234"),
        ("feature/issue-1234-add-a-great-feature", "1234"),
    ],
)
def test_branch_formatter_regexp(repo, template_config, create_config, branch, suffix):
    checkout_branch(repo, branch)

    template_config(
        repo,
        create_config,
        template="{tag}{branch}{ccount}",
        config={
            "branch_formatter": r".*?(?P<branch>[\d]+).*",
        },
    )

    assert get_version(repo) == f"1.2.3{suffix}0"


def test_branch_formatter_regexp_not_match(repo, template_config, create_config):
    checkout_branch(repo, "unknown")

    template_config(
        repo,
        create_config,
        template="{tag}{branch}{ccount}",
        config={
            "branch_formatter": r".*?(?P<branch>[\d]+).*",
        },
    )

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)


@pytest.mark.parametrize("regexp", [r".*?([\d]+).*", r".*?(?P<unknown>[\d]+).*"])
def test_branch_formatter_regexp_no_capture_group(repo, template_config, create_config, regexp):
    template_config(
        repo,
        create_config,
        config={
            "branch_formatter": regexp,
        },
    )

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)


def test_branch_formatter_regexp_wrong_format(repo, template_config, create_config):
    template_config(
        repo,
        create_config,
        config={
            "branch_formatter": "(",
        },
    )

    with pytest.raises(subprocess.CalledProcessError):
        get_version(repo)


@pytest.mark.parametrize(
    "version_callback",
    ["version:get_version", "version:__version__"],
)
def test_branch_formatter_ignored_if_version_callback_set(repo, create_config, version_callback):
    create_file(
        repo,
        "version.py",
        textwrap.dedent(
            """
            def get_version():
                return "1.0.0"

            __version__ = "1.0.0"
            """
        ),
    )
    create_config(
        repo,
        {
            "version_callback": version_callback,
            "branch_formatter": "(",
        },
    )

    assert get_version(repo) == "1.0.0"
