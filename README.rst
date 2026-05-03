*************************
setuptools-git-versioning
*************************

|status| |PyPI| |PyPI License| |PyPI Python Version|
|ReadTheDocs| |Build| |Coverage| |pre-commit.ci|

.. |status| image:: https://www.repostatus.org/badges/latest/active.svg
    :alt: Project Status: Active – The project has reached a stable, usable state and is being actively developed.
    :target: https://www.repostatus.org/#active
.. |PyPI| image:: https://badge.fury.io/py/setuptools-git-versioning.svg
    :target: https://badge.fury.io/py/setuptools-git-versioning
.. |PyPI License| image:: https://img.shields.io/pypi/l/setuptools-git-versioning.svg
    :target: https://github.com/dolfinus/setuptools-git-versioning/blob/master/LICENSE
.. |PyPI Python Version| image:: https://img.shields.io/pypi/pyversions/setuptools-git-versioning.svg
    :target: https://badge.fury.io/py/setuptools-git-versioning
.. |ReadTheDocs| image:: https://img.shields.io/readthedocs/setuptools-git-versioning.svg
    :target: https://setuptools-git-versioning.readthedocs.io
.. |Build| image:: https://github.com/dolfinus/setuptools-git-versioning/workflows/Tests/badge.svg
    :target: https://github.com/dolfinus/setuptools-git-versioning/actions
.. |Coverage| image:: https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/
    dolfinus/38b81533c2b8c389db378e3bae7df034/raw/setuptools_git_versioning_badge.json
    :target: https://github.com/dolfinus/setuptools-git-versioning/actions
.. |pre-commit.ci| image:: https://results.pre-commit.ci/badge/github/dolfinus/setuptools-git-versioning/master.svg
    :target: https://results.pre-commit.ci/latest/github/dolfinus/setuptools-git-versioning/master

Use git repo data (latest tag, current commit hash, etc) for building a
version number according to :pep:`440`.

**Features:**

- Can be installed & configured through both ``setup.py`` and :pep:`518`'s ``pyproject.toml``

- Does not require to change source code of the project

- Tag-, file-, and callback-based versioning schemas are supported

- Templates for *tag*, *dev* and *dirty* versions are separated

- Templates support a lot of substitutions including git and environment information

- Well-documented

See `comparison <https://setuptools-git-versioning.readthedocs.io/en/stable/comparison.html>`_
between ``setuptools-git-versioning`` and other tools.

**Limitations:**

- Currently the only supported VCS is *Git*

- Only Git v2 is supported

- Setuptools and `scikit-build-core <https://scikit-build-core.readthedocs.io>`_ build backends are
  supported (no Poetry & others)

- Currently does not support automatic exporting of package version to a file for runtime use
  (but you can use ``setuptools-git-versioning > file`` redirect instead)

.. documentation

Documentation
--------------

See https://setuptools-git-versioning.readthedocs.io/en/stable/

.. installation

Install
------------

``pyproject.toml``
~~~~~~~~~~~~~~~~~~

Just add ``setuptools-git-versioning`` to ``build-sytem`` section of your ``pyproject.toml``,
add a section ``tool.setuptools-git-versioning`` with config options, and mark the project
``version`` as dynamic.

.. code:: toml

    [build-system]
    requires = [ "setuptools>=41", "wheel", "setuptools-git-versioning>=3.0,<4", ]
    build-backend = "setuptools.build_meta"

    [tool.setuptools-git-versioning]
    enabled = true

    [project]
    dynamic = ["version"]

And check the package version generated (see `command help <https://setuptools-git-versioning.readthedocs.io/en/stable/command.html>`_):

.. code:: bash

    $ python -m setuptools_git_versioning
    0.0.1

    # or

    $ setuptools-git-versioning
    0.0.1

When add a git tag:

.. code:: bash

    $ git add .
    $ git commit -m "Test tagged"
    $ git tag 1.2.3

And now version is based on git tag:

.. code:: bash

    $ setuptools-git-versioning
    1.2.3

    $ echo 1 > uncommitted.change
    $ git add .
    $ setuptools-git-versioning
    1.2.3.post0+git.d2bc6516.dirty

    $ git commit -m "Test committed"
    $ setuptools-git-versioning
    1.2.3.post1+git.d452190b


``setup.py``
~~~~~~~~~~~~

Just add ``setuptools-git-versioning`` to ``setup_requires`` argument of ``setuptools.setup`` function call,
and then add new argument ``setuptools_git_versioning`` with config options:

.. code:: python

    import setuptools

    setuptools.setup(
        ...,
        setuptools_git_versioning={
            "enabled": True,
        },
        setup_requires=["setuptools-git-versioning>=3.0,<4"],
    )

Commands are the same as above, plus ``python -m setup.py`` returns the same version.

``scikit-build-core``
~~~~~~~~~~~~~~~~~~~~~

If your project uses the `scikit-build-core <https://scikit-build-core.readthedocs.io>`_ build backend,
add ``setuptools-git-versioning`` to ``build-system.requires``,
mark the ``version`` field as dynamic,
register the dynamic-metadata provider,
and configure options under the usual ``[tool.setuptools-git-versioning]`` section:

.. code:: toml

    [build-system]
    requires = [ "scikit-build-core", "setuptools-git-versioning>=3.0,<4", ]
    build-backend = "scikit_build_core.build"

    [project]
    name = "mypackage"
    dynamic = ["version"]

    [tool.scikit-build.metadata.version]
    provider = "setuptools_git_versioning.scikit_metadata"

    [tool.setuptools-git-versioning]
    enabled = true

All options under ``[tool.setuptools-git-versioning]`` work exactly as the setuptools backend.
Inline configuration under ``[tool.scikit-build.metadata.version]`` is not supported.
