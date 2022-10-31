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
.. |Coverage| image:: https://codecov.io/gh/dolfinus/setuptools-git-versioning/branch/master/graph/badge.svg?token=GIMVHUTNW4
    :target: https://codecov.io/gh/dolfinus/setuptools-git-versioning
.. |pre-commit.ci| image:: https://results.pre-commit.ci/badge/github/dolfinus/setuptools-git-versioning/master.svg
    :target: https://results.pre-commit.ci/latest/github/dolfinus/setuptools-git-versioning/master

Use git repo data (latest tag, current commit hash, etc) for building a
version number according :pep:`440`.

**Features:**

- Can be installed & configured through both ``setup.py`` and :pep:`518`'s ``pyproject.toml``

- Does not require to change source code of the project

- Tag-, file-, and callback-based versioning schemas are supported

- Templates for *tag*, *dev* and *dirty* versions are separated

- Templates support a lot of substitutions including git and environment information

- Well-documented

See `difference <https://setuptools-git-versioning.readthedocs.io/en/latest/differences.html>`_
between ``setuptools-git-versioning`` and other tools.

**Limitations:**

- Currently the only supported VCS is *Git*

- Only git v2 is supported

- Currently does not support automatic exporting of package version to a file for runtime use
  (but you can use ``setuptools-git-versioning > file`` redirect instead)

.. documentation

Documentation
--------------

See https://setuptools-git-versioning.readthedocs.io/en/stable/

.. contribution

Contribution Guide
------------------

See ./CONTRIBUTING.rst

.. installation

Install
------------

``pyproject.toml``
~~~~~~~~~~~~~~~~~~

Just add ``setuptools-git-versioning`` to ``build-sytem`` section of your ``pyproject.toml``,
and a section ``tool.setuptools-git-versioning`` with config options:

.. code:: toml

    [build-system]
    requires = [ "setuptools>=41", "wheel", "setuptools-git-versioning<2", ]
    build-backend = "setuptools.build_meta"

    [tool.setuptools-git-versioning]
    enabled = true

And check the package version generated (see `command help <https://setuptools-git-versioning.readthedocs.io/en/stable/command.html>`__):

.. code:: bash

    $ python -m setuptools_git_versioning
    0.0.1

    # or

    $ setuptools-git-versioning
    0.0.1

``setup.py``
~~~~~~~~~~~~~~

Just add ``setuptools-git-versioning`` to ``setup_requires`` argument of ``setuptools.setup`` function call,
and then add new argument ``setuptools_git_versioning`` with config options:

.. code:: python

    import setuptools

    setuptools.setup(
        ...,
        setuptools_git_versioning={
            "enabled": True,
        },
        setup_requires=["setuptools-git-versioning<2"],
    )

And check the package version generated (see `command help <https://setuptools-git-versioning.readthedocs.io/en/stable/command.html>`__):

.. code:: bash

    $ python setup.py --version
    0.0.1

    # or

    $ python -m setuptools_git_versioning
    0.0.1

    # or

    $ setuptools-git-versioning
    0.0.1
