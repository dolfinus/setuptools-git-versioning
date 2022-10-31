Changelog
==========

1.13
----

.. changelog::
    :version: 1.13.0

    .. change::
        :tags: dependencies, feature

        For Python 3.11 use built-in ``tomllib`` instead of ``toml`` package

    .. change::
        :tags: docs, feature

        Add documentation about fetching package version in runtime

    .. change::
        :tags: core, breaking

        Make all internal functions private

    .. change::
        :tags: docs, feature

        Add description for some functions

1.12
----

.. changelog::
    :version: 1.12.1
    :released: 24.10.2022

    .. change::
        :tags: core, bug

        Make version sanitization less strict, allow to automatically convert some cases, e.g.
        ``1.0.0+feature/abc`` to ``1.0.0+feature.abc``

.. changelog::
    :version: 1.12.0
    :released: 13.10.2022

    .. change::
        :tags: core, breaking

        Sanitize ``starting_version`` according :pep:`440`

    .. change::
        :tags: core, breaking

        Do not remove leading non-numeric symbols from version number (except ``v``)

1.11
----

.. changelog::
    :version: 1.11.0
    :released: 02.10.2022

    .. change::
        :tags: core, feature

        Allow ``setuptools-git-versioning`` script to infer version from ``setup.py`` if ``pyproject.toml`` is missing

    .. change::
        :tags: core, breaking

        Raise error if ``pyproject.toml`` exists, but is not a file

    .. change::
        :tags: core, feature

        Add ``cwd`` argument to most of functions, allowing to get versions of a specific repo without changing current directory

    .. change::
        :tags: dev, feature

        Add info and debug messages to the module

    .. change::
        :tags: docs, feature

        Add documentation for ``setuptools-git-versioning`` script

    .. change::
        :tags: tests, refactoring

        Use builtin type annotations (instead of type comments) in ``tests/lib/util.py``,
        use modern annotations syntax (``type | None`` instead of ``Optional[type]``)

1.10
----

.. changelog::
    :version: 1.10.1
    :released: 03.09.2022

    .. change::
        :tags: core, feature

        Add ``setuptools-git-versioning`` script to infer version from ``pyproject.toml`` config

    .. change::
        :tags: core, feature

        Check Python 3.11 support

.. changelog::
    :version: 1.10.0
    :released: 18.07.2022

    .. change::
        :tags: core, breaking

        :ref:`version-callback-option` option is used even if there are some tags in the current branch

    .. change::
        :tags: config, feature

        Raise exception if both :ref:`version-callback-option` and :ref:`version-file-option` options are set

    .. change::
        :tags: core, feature

        Remove all non-numeric symbols from version prefix, not just ``v``

    .. change::
        :tags: core, feature

        Check :ref:`version-callback-option` option before checking a tag presence

1.9
----

.. changelog::
    :version: 1.9.2
    :released: 21.03.2022

    .. change::
        :tags: general

        Add ``setup_requires`` item to ``setup.py``

.. changelog::
    :version: 1.9.1
    :released: 21.03.2022

    .. change::
        :tags: general

        Remove ``pyproject.toml`` file from ``.tag.gz`` package

.. changelog::
    :version: 1.9.0
    :released: 21.03.2022

    .. change::
        :tags: general, breaking

        Drop Python 2.7, 3.5 and 3.6 support. Minimal supported Python version is now 3.7

    .. change::
        :tags: core, feature

        Do not fail on ``toml`` and ``packaging`` modules import while installing ``setuptools-git-versioning`` from ``tag.gz`` file

    .. change::
        :tags: ci, bug

        Fix creating multiple releases for the same tag

1.8
----

.. changelog::
    :version: 1.8.1
    :released: 10.01.2022

    .. change::
        :tags: core, bug

        Fix issue with empty ``pyproject.toml``

.. changelog::
    :version: 1.8.0
    :released: 07.01.2022

    .. change::
        :tags: general, breaking
        :pullreq: 37

        Drop Python 3.3 and 3.4 support

    .. change::
        :tags: general, deprecated

        Python 2.7, 3.5 and 3.6 support is deprecated due to their end of life.

        It will be completely removed in ``2.0.0`` release. A warning message is added

    .. change::
        :tags: core, deprecated

        ``get_branch_tags`` function is renamed to ``get_tags``.

        It will be removed in ``2.0.0`` release. A warning message is added

    .. change::
        :tags: config, deprecated

        ``version_config`` keyword in ``setup.py`` is renamed to ``setuptools_git_versioning``.

        It will be removed in ``2.0.0`` release. A warning message is added

    .. change::
        :tags: config, deprecated

        Prefer using ``"enabled": True`` / ``"enabled": False`` option
        instead of pure boolean values (``True``, ``False``) for config.

        Old behavior is deprecated and will be removed in ``2.0`` version. A warning message is added

    .. change::
        :tags: core, feature
        :pullreq: 37
        :tickets: 35

        Add support of reading config from ``pyproject.toml``.

        Thanks to :github-user:`Bloodmallet`

    .. change::
        :tags: core, feature

        Allow to pass regexp to ``branch_formatter`` option

    .. change::
        :tags: core, feature
        :tickets: 31

        Add ``tag_formatter`` option

    .. change::
        :tags: core, feature

        Allow nested default values to be passed to ``env`` substitution

    .. change::
        :tags: tests, feature

        Add integration tests

    .. change::
        :tags: ci, feature

        Check test coverage and fail if it has been decreased

    .. change::
        :tags: ci, feature

        Build docs using ReadTheDocs project

    .. change::
        :tags: docs, feature

        Major docs improvement

    .. change::
        :tags: docs, feature

        Added CHANGELOG.rst

    .. change::
        :tags: docs

        Add ``miniver`` and ``versioningit`` to comparison table

1.7
----

.. changelog::
    :version: 1.7.4
    :released: 31.10.2021

    .. change::
        :tags: ci, feature
        :changeset: ac47f210

        Change release workflow action from ``actions/create-release@v1``
        to ``softprops/action-gh-release@v1``

.. changelog::
    :version: 1.7.3
    :released: 31.10.2021

    .. change::
        :tags: ci, feature
        :changeset: a7af368f

        Change release workflow action from ``actions/create-release@v1``
        to ``softprops/action-gh-release@v1``

.. changelog::
    :version: 1.7.2
    :released: 28.10.2021

    .. change::
        :tags: core, feature
        :tickets: 29
        :changeset: c2ed0da8

        String leading 'v' symbol from tag name

.. changelog::
    :version: 1.7.1
    :released: 28.10.2021

    .. change::
        :tags: core, feature
        :tickets: 29
        :changeset: b2da6fbc

        String leading 'v' symbol from tag name

.. changelog::
    :version: 1.7.0
    :released: 21.09.2021

    .. change::
        :tags: core, feature

        Add support of ``env`` variables substitution

    .. change::
        :tags: core, feature

        Add support of ``timestamp`` substitution


1.6
----

.. changelog::
    :version: 1.6.1
    :released: 16.09.2021

    .. change::
        :tags: core, bug
        :changeset: f59518bf
        :tickets: 23

        Fix sorting for annotated tags

.. changelog::
    :version: 1.6.0
    :released: 15.09.2021

    .. change::
        :tags: ci, bug
        :changeset: f43e6aa4

        Fix skipping duplicated runs

    .. change::
        :tags: ci, feature
        :changeset: 543615ba

        Add automerge action for ``precommit-ci ``bot

    .. change::
        :tags: ci, bug
        :changeset: e9e13e93

        Fix tests workflow

    .. change::
        :tags: core, bug
        :changeset: 22bc1db8
        :tickets: 22

        Sort tags by commit date instead of name

    .. change::
        :tags: ci, bug
        :changeset: c081fb9ca

        Fix release pipeline



1.5
----

.. changelog::
    :version: 1.5.0
    :released: 16.08.2021

    .. change::
        :tags: docs
        :changeset: 147abff1
        :tickets: 15

        Add ``setuptools-scm`` and ``versioneer`` to comparison table

    .. change::
        :tags: docs, feature
        :changeset: d81106fc
        :tickets: 17
        :pullreq: 16

        Add resolution for issue when all versions produced by CI pipeline are ``dirty``

    .. change::
        :tags: ci, feature
        :changeset: 42f6f066

        Skip duplicated Github Actions runs

    .. change::
        :tags: dev, feature
        :changeset: be88c2ac

        Add ``pre-commit`` hooks and commit changes made by it


1.4
----

.. changelog::
    :version: 1.4.0
    :released: 12.05.2021

    .. change::
        :tags: ci, bug
        :changeset: b680f53f

        Use absolute paths in ``setup.py``

    .. change::
        :tags: dev, bug
        :changeset: 55b8e706
        :pullreq: 13

        Add JetBrains config files to ``.gitignore``.

        Thanks to :github-user:`LeComptoirDesPharmacies`

    .. change::
        :tags: core, feature
        :changeset: c9cafa22
        :pullreq: 14

        Add ``branch_formatter`` option.

        Thanks to :github-user:`LeComptoirDesPharmacies`


1.3
----

.. changelog::
    :version: 1.3.6
    :released: 12.03.2021

    .. change::
        :tags: general, bug
        :changeset: ffebe6f0

        Update package short description

    .. change::
        :tags: general
        :changeset: ffebe6f0

        Set license in ``setup.py`` file

.. changelog::
    :version: 1.3.5
    :released: 12.03.2021

    .. change::
        :tags: docs, bug
        :changeset: 7ae433d6

        Fix comparison table typo

    .. change::
        :tags: docs, feature
        :changeset: 813ef149

        Add license column into comparison table

.. changelog::
    :version: 1.3.4
    :released: 12.03.2021

    .. change::
        :tags: docs, feature
        :changeset: 0023523b

        Add list of supported substitutions into comparison table

    .. change::
        :tags: docs
        :changeset: 7143b97f

        Add ``bad-setuptools-git-version`` and ``another-setuptools-git-version``
        to comparison table

.. changelog::
    :version: 1.3.3
    :released: 12.03.2021

    .. change::
        :tags: core, bug
        :changeset: 44bd8fd5
        :pullreq: 11

        Replace forbidden chars in local version label.

        Thanks to :github-user:`ajasmin`

.. changelog::
    :version: 1.3.2
    :released: 12.03.2021

    .. change::
        :tags: docs, bug

        Fix minor typos in documentation

.. changelog::
    :version: 1.3.1
    :released: 12.03.2021

    .. change::
        :tags: docs, feature
        :changeset: cc5b03e2
        :tickets: 8

        Add Windows support column into comparison table

    .. change::
        :tags: ci, bug
        :changeset: bc87c4f2

        Fix Github Actions

    .. change::
        :tags: core, bug
        :changeset: 64e68cd4
        :tickets: 10

        Replace default suffix for dev and dirty versions from ``dev`` to ``post``

    .. change::
        :tags: docs, feature
        :changeset: adf997c0
        :tickets: 10

        Major documentation update

.. changelog::
    :version: 1.3.0
    :released: 01.03.2021

    .. change::
        :tags: core, feature
        :changeset: 5ac7d8fd
        :tickets: 9

        Add ``full_sha`` substitution support


1.2
----

.. changelog::
    :version: 1.2.10
    :released: 04.02.2021

    .. change::
        :tags: ci, bug
        :changeset: e05f970c
        :pullreq: 7

        Fix release workflow

    .. change::
        :tags: ci, feature
        :changeset: 7a51e76c
        :pullreq: 7

        Add some issue and PR automatization

    .. change::
        :tags: core, bug
        :changeset: 96843236
        :tickets: 8

        Fix Windows compatibility

.. changelog::
    :version: 1.2.9
    :released: 20.01.2021

    .. change::
        :tags: ci, feature
        :changeset: 6848c244
        :pullreq: 7

        Use Github Actions instead of TravisCI

.. changelog::
    :version: 1.2.8
    :released: 29.11.2020

    .. change::
        :tags: docs, bug
        :changeset: 89478a04
        :pullreq: 6

        Fixed typo in code examples.

        Thanks to :github-user:`Stedders`

.. changelog::
    :version: 1.2.7
    :released: 24.11.2020

    .. change::
        :tags: core, bug
        :changeset: b808b01a
        :pullreq: 5

        Fix python error if no tag is found.

        Thanks to :github-user:`bmiklautz`

.. changelog::
    :version: 1.2.6
    :released: 07.10.2020

    .. change::
        :tags: core, bug
        :changeset: bc7e3500

        Fix version detection in case of missing .git folder

.. changelog::
    :version: 1.2.5
    :released: 30.09.2020

    .. change::
        :tags: dependency, bug
        :changeset: 07addd87

        Fix Python 2.7 dependencies

.. changelog::
    :version: 1.2.4
    :released: 30.09.2020

    .. change::
        :tags: dependency, bug
        :changeset: 07b92afc

        Fix Python 2.7 dependencies

.. changelog::
    :version: 1.2.3
    :released: 16.09.2020

    .. change::
        :tags: core, feature
        :changeset: bee32404

        Add ``get_all_tags`` function

    .. change::
        :tags: core, feature
        :changeset: 1ed862d0

        Add ``get_branch_tags`` function

.. changelog::
    :version: 1.2.2
    :released: 14.09.2020

    .. change::
        :tags: core, bug
        :changeset: 1ed862d0

        Fix building version from VERSION file

.. changelog::
    :version: 1.2.1
    :released: 10.09.2020

    .. change::
        :tags: core, feature
        :changeset: 5a47ac43

        Add ``count_commits_from_version_file`` option

.. changelog::
    :version: 1.2.0
    :released: 10.09.2020

    .. change::
        :tags: core, feature
        :changeset: 5c4dd0f2

        Add ``version_file`` option


1.1
----
.. changelog::
    :version: 1.1.14
    :released: 10.09.2020

    .. change::
        :tags: core, feature
        :changeset: 4bce22ab

        Add ``version_callback`` option

.. changelog::
    :version: 1.1.13
    :released: 21.08.2020

    .. change::
        :tags: ci, bug
        :changeset: 4d57008d
        :tickets: 4

        Use ``six`` module for accessing ``collections.abc``

.. changelog::
    :version: 1.1.12
    :released: 20.08.2020

    .. change::
        :tags: ci, bug
        :changeset: b85a5e5d
        :tickets: 4

        Fix package name misspell

.. changelog::
    :version: 1.1.11
    :released: 18.08.2020

    .. change::
        :tags: dependency, bug
        :changeset: 184e9670

        Remove ``flake8`` from ``requirements.txt``

.. changelog::
    :version: 1.1.10
    :released: 18.08.2020

    .. change::
        :tags: dependency, bug
        :changeset: 119f98a0

        Make ``setuptools`` version check less strict

.. changelog::
    :version: 1.1.9
    :released: 17.08.2020

    .. change::
        :tags: general, feature
        :changeset: 2fde432b

        Test Python 3.9 support

    .. change::
        :tags: ci, bug
        :changeset: b07d4af6
        :tickets: 3

        Include ``requirements.txt`` into ``.tar.gz`` file

.. changelog::
    :version: 1.1.8
    :released: 14.08.2020

    .. change::
        :tags: general, feature
        :changeset: f9dfa1e6

        Add Python 3.3 and 3.4 support

.. changelog::
    :version: 1.1.7
    :released: 10.08.2020

    .. change::
        :tags: ci, bug
        :changeset: 777c1366

        Fix TravisCI deploy

.. changelog::
    :version: 1.1.6

    .. change::
        :tags: core, feature
        :changeset: f444bdd8

        Add backward compatibility with ``git`` < 2.2

    .. change::
        :tags: docs, feature
        :changeset: 1686d25c

        Add supported python versions badge

.. changelog::
    :version: 1.1.5
    :released: 07.08.2020

    .. change::
        :tags: core, bug
        :changeset: 8d427b31
        :pullreq: 1

        Fix runtime error on Python 3.3 and 3.4.

        Thanks to :github-user:`WildCard65`

.. changelog::
    :version: 1.1.4
    :released: 07.08.2020

    .. change::
        :tags: core, feature
        :changeset: 3c213500

        Add ``branch`` substitution support

.. changelog::
    :version: 1.1.3
    :released: 30.07.2020

    .. change::
        :tags: core, feature
        :changeset: 85439b40

        Add ``starting_version`` option

    .. change::
        :tags: ci, bug
        :changeset: b2293faa

        Fix TravisCI build

.. changelog::
    :version: 1.1.2
    :released: 29.07.2020

    .. change::
        :tags: ci, bug
        :changeset: 98323c6c

        Fix Python 2 version build

    .. change::
        :tags: dependency, bug
        :changeset: 2966d03a

        Fix ``requirements.txt``

.. changelog::
    :version: 1.1.1

    .. change::
        :tags: general, feature
        :changeset: 7022ef37

        Change package name to ``setuptools-git-versioning`` and publish it on PyPi.org

.. changelog::
    :version: 1.1.0

    .. change::
        :tags: general
        :changeset: ad72cb72

        Create fork of unmaintained repo `setuptools-git-ver <https://github.com/camas/setuptools-git-ver>`_

    .. change::
        :tags: core, feature
        :changeset: fd1fff57

        Added Python2 support.

        Typehints moved to comments section.
        Python 3 syntax replaced with Python 2 compatible one

    .. change::
        :tags: core, feature
        :changeset: b133dce5

        Make internal functions public

    .. change::
        :tags: core, feature
        :changeset: 2693ef5b

        Add ``get_tags`` method
