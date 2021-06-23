import os
from setuptools import setup, find_packages
from setuptools_git_versioning import version_from_git

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "README.md"), "r") as f:
    long_description = f.read()

with open(os.path.join(HERE, "requirements.txt"), "r") as f:
    requirements = f.read().split("\n")

setup(
    name="lcdp-setuptools-git-versioning",
    version=version_from_git(),
    author="Camas",
    author_email="camas@hotmail.co.uk",
    maintainer="dolfinus",
    maintainer_email="martinov.m.s.8@gmail.com",
    description="Use git repo data for building a version number according PEP-440",
    license='MIT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LeComptoirDesPharmacies/setuptools-git-versioning",
    keywords='setuptools git version-control',
    packages=find_packages(),
    classifiers=[
        'Framework :: Setuptools Plugin',
        'Intended Audience :: Developers',
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7,!=3.1,!=3.2',
    py_modules=['setuptools_git_versioning'],
    install_requires=requirements,
    entry_points={
        'distutils.setup_keywords': [
            'version_config = setuptools_git_versioning:parse_config',
        ],
    },
    include_package_data=True,
    zip_safe=False
)
