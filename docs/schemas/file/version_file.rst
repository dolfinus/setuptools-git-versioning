.. _version-file:

Read some file content as current version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For example, current repo state is:

.. code:: bash

    commit 233f6d72 Dev branch commit (HEAD, dev)
    |
    |    commit 86269212 Release commit (v1.0.0, master)
    |    |
    |   commit e7bdbe51 Another commit
    |    /
    ...
    |
    commit 273c47eb Long long ago
    |
    ...

By default, when you try to get current version, you'll receive some
initial value (see :ref:`starting-version-option` option).

But if you want to get synchronized version numbers in
both on the branches, you can create a text file and save here current version number:

.. code-block:: txt
    :caption: mymodule/VERSION

    1.0.0

Then place it in both the branches and update your config file:

.. tabs::

    .. code-tab:: python ``setup.py``

        import setuptools
        from pathlib import Path

        root_path = Path(__file__).parent
        version_file = root_path / "VERSION"

        setuptools.setup(
            ...,
            setup_requires=["setuptools-git-versioning>=3.0,<4"],
            setuptools_git_versioning={
                "enabled": True,
                "version_file": version_file,  # <---
            },
        )

    .. code-tab:: toml ``pyproject.toml``

        [build-system]
        requires = [ "setuptools>=41", "wheel", "setuptools-git-versioning>=3.0,<4", ]
        build-backend = "setuptools.build_meta"

        [tool.setuptools-git-versioning]
        enabled = true
        version_file = "VERSION"  # <---

When you'll try to get current version in non-master branch, the content
of this file (``1.0.0``) will be returned instead default version number.

**Please take into account that any tags in the repo are ignored if this option is being used.**

.. note::

    If you want the latest Git tag to take precedence over the version file
    (for example, when a release tag like ``v2.1.0rc1`` is pushed but the
    version file still contains ``2.1.0``), set the
    :ref:`prefer-tag-option` option to ``true``.

See also
"""""""""
- :ref:`version-callback`
- :ref:`version-file-option` option
- :ref:`prefer-tag-option` option
- :ref:`runtime-version`
