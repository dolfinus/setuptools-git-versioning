from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup

from setuptools_git_versioning import version_from_git


def parse_requirements(file: Path) -> list[str]:
    lines = file.read_text().splitlines()
    return [line.rstrip() for line in lines if line and not line.startswith("#")]


here = Path(__file__).parent.resolve()
requirements = parse_requirements(here / "requirements.txt")
long_description = here.joinpath("README.rst").read_text()

setup(
    name="setuptools-git-versioning",
    # +local version is not allowed in PyPI
    # https://github.com/pypa/pypi-legacy/issues/731#issuecomment-345461596
    version=version_from_git(root=here, dev_template="{tag}.post{ccount}"),
    author="dolfinus",
    author_email="martinov.m.s.8@gmail.com",
    description="Use git repo data for building a version number according to PEP-440",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://setuptools-git-versioning.readthedocs.io",
    keywords=["setuptools", "git", "versioning", "pep-440"],
    packages=find_packages(exclude=["docs", "tests", "docs.*", "tests.*"]),
    classifiers=[
        "Framework :: Setuptools Plugin",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Documentation": "https://setuptools-git-versioning.readthedocs.io",
        "Source": "https://github.com/dolfinus/setuptools-git-versioning",
        "CI/CD": "https://github.com/dolfinus/setuptools-git-versioning/actions",
        "Coverage": "https://app.codecov.io/gh/dolfinus/setuptools-git-versioning",
        "Tracker": "https://github.com/dolfinus/setuptools-git-versioning/issues",
    },
    python_requires=">=3.7",
    py_modules=["setuptools_git_versioning"],
    install_requires=requirements,
    setup_requires=requirements,
    entry_points={
        "distutils.setup_keywords": [
            "setuptools_git_versioning = setuptools_git_versioning:parse_config",
        ],
        "setuptools.finalize_distribution_options": [
            "setuptools_git_versioning = setuptools_git_versioning:infer_version",
        ],
        "console_scripts": ["setuptools-git-versioning=setuptools_git_versioning:__main__"],
    },
    include_package_data=True,
    zip_safe=False,
)
