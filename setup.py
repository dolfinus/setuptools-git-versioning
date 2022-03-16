import os
import sys

from setuptools import find_packages, setup

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)


from setuptools_git_versioning import version_from_git  # noqa: E402


def parse_requirements(file_content):
    lines = file_content.splitlines()
    return [line.strip() for line in lines if line and not line.startswith("#")]


with open(os.path.join(HERE, "README.rst")) as f:
    long_description = f.read()

with open(os.path.join(HERE, "requirements.txt")) as f:
    requirements = parse_requirements(f.read())

setup(
    name="setuptools-git-versioning",
    version=version_from_git,
    author="dolfinus",
    author_email="martinov.m.s.8@gmail.com",
    description="Use git repo data for building a version number according PEP-440",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://setuptools-git-versioning.readthedocs.io",
    keywords="setuptools git version-control",
    packages=find_packages(exclude=["docs", "tests", "docs.*", "tests.*"]),
    classifiers=[
        "Framework :: Setuptools Plugin",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
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
    python_requires=">=2.7,!=3.1,!=3.2,!=3.3,!=3.4",
    py_modules=["setuptools_git_versioning"],
    install_requires=requirements,
    entry_points={
        "distutils.setup_keywords": [
            "version_config = setuptools_git_versioning:parse_config",
            "setuptools_git_versioning = setuptools_git_versioning:parse_config",
        ],
        "setuptools.finalize_distribution_options": [
            "setuptools_git_versioning = setuptools_git_versioning:infer_version",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
