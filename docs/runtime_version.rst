.. _runtime-version:

Retrieving package version at runtime
-------------------------------------

Using ``version_file`` or ``version_callback`` options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The preferred way to set version number inside a package is
to simply store it in some file or variable/function, and
then use it in ``setup.py`` / ``pyproject.toml`` as version source.

It this case you can get current version without any access to ``.git`` folder
(which is required by ``setuptools-git-versioning``).

See:

* :ref:`version-file`
* :ref:`version-callback`

Using ``importlib``
~~~~~~~~~~~~~~~~~~~

If you have opted not to hardcode the version number inside the package,
you can retrieve it at runtime from :pep:`0566` metadata using
``importlib.metadata`` from the standard library (added in Python 3.8)
or the `importlib_metadata`_ backport:

.. code:: python

    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("package-name")
    except PackageNotFoundError:
        # package is not installed
        pass

.. _importlib_metadata: https://pypi.org/project/importlib-metadata/

Using ``pkg_resources``
~~~~~~~~~~~~~~~~~~~~~~~

In some cases ``importlib`` cannot properly detect package version,
for example it was compiled into executable file, so it uses some
custom import mechanism.

Instead, you can use ``pkg_resources`` which is included in ``setuptools``
(but has a significant runtime cost):

.. code:: python

    from pkg_resources import get_distribution, DistributionNotFound

    try:
        __version__ = get_distribution("package-name").version
    except DistributionNotFound:
        # package is not installed
        pass

However, this does place a runtime dependency on setuptools,
and can add up to a few 100ms overhead for the package import time.

Calling internals of ``setuptools_git_versioning`` module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

  This way is STRONGLY DISCOURAGED. Functions in the module
  are not a part of public API, and could be changed in the future without
  maintaining backward compatibility.

.. warning::

  Use this ONLY in CI/CD tools.

  NEVER use ``setuptools_git_versioning`` inside your package, because ``.git``
  folder is not being included into it, and target OS can lack of ``git`` executable.

  ``.git`` folder and ``git`` executable presence is crucial
  for ``setuptools-git-versioning`` to work properly.

.. code:: python

    from setuptools_git_versioning import get_version

    # uses setup.py or pyproject.toml as config source
    version = get_version()

    from setuptools_git_versioning import get_tag, get_all_tags

    # calls `git` executable to get latest tag merged into HEAD history tree
    latest_tag = get_tag()

    # calls `git` executable to get all the tags in the repo
    all_tags = get_all_tags()
