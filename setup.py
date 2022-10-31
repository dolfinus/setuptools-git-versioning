import os
from setuptools import setup, find_packages
from setuptools_git_versioning import version_from_git

HERE = os.path.dirname(os.path.abspath(__file__))


def parse_requirements(file_content):
    lines = file_content.splitlines()
    return [line.strip() for line in lines if line and not line.startswith("#")]


with open(os.path.join(HERE, "README.rst")) as f:
    long_description = f.read()

with open(os.path.join(HERE, "requirements.txt")) as f:
    requirements = parse_requirements(f.read())

setup(
    name="setuptools-git-versioning",
    version=version_from_git(root=HERE),
    author="dolfinus",
    author_email="martinov.m.s.8@gmail.com",
    description="Use git repo data for building a version number according PEP-440",
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
            "version_config = setuptools_git_versioning:_parse_config",
            "setuptools_git_versioning = setuptools_git_versioning:_parse_config",
        ],
        "setuptools.finalize_distribution_options": [
            "setuptools_git_versioning = setuptools_git_versioning:_infer_version",
        ],
        "console_scripts": ["setuptools-git-versioning=setuptools_git_versioning:__main__"],
    },
    include_package_data=True,
    zip_safe=False,
)
