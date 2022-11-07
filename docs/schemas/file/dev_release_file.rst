.. _dev-release-file:

Development releases (prereleases) from ``dev`` branch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

**And there are no tags in the current branch** (``dev``), **all
of them are placed in the** ``master`` **branch.**

If you want to create development releases (prereleases) for the next planned version ``1.1.0``,
so every commit to ``dev`` branch should produce version number like ``1.1.0.dev123`` (just plain increment)
or even ``1.1.0.dev123+git.sha`` (to describe which commit was used for this exact version).

In such a case you need to create a text file (for example, ``VERSION`` or ``VERSION.txt``)
with your **next release number** (e.g. ``1.1.0``):

.. code:: txt

    1.1.0

Then update your config file:

- ``setup.py`` :

    .. code:: python

        import os

        HERE = os.path.dirname(__file__)
        VERSION_FILE = os.path.join(HERE, "VERSION.txt")

        setuptools.setup(
            ...,
            setuptools_git_versioning={
                "enabled": True,
                "version_file": VERSION_FILE,
                "count_commits_from_version_file": True,  # enable commits tracking
                "dev_template": "{tag}.dev{ccount}",  # suffix for versions will be .dev
                "dirty_template": "{tag}.dev{ccount}",  # same thing here
            },
        )

- ``pyproject.toml``:

    .. code:: toml

        [tool.setuptools-git-versioning]
        enabled = true
        version_file = "VERSION"
        count_commits_from_version_file = true
        dev_template = "{tag}.dev{ccount}"
        dirty_template = "{tag}.dev{ccount}"

In case of next release version ``1.1.0`` the third commit to ``dev`` branch will produce
version number ``1.1.0.dev3``, and so on.

Release process
""""""""""""""""

-  Merge ``dev`` branch into ``master`` branch.
-  Tag commit in the ``master`` branch with next release version (e.g. ``1.1.0``). Tag will be used as a version number for the release.

    .. warning::

        Do not place any tags in the ``dev`` branch!

-  Checkout back to ``dev`` branch
-  Save next release version (e.g. ``1.2.0``) in ``VERSION`` or ``VERSION.txt`` file in the ``dev`` branch.

-  Next commits to a ``dev`` branch will lead to returning this next release version plus dev suffix, like ``1.2.0.dev1`` or so.
-  ``N`` in ``.devN`` suffix is a number of commits since the last change of a certain file.

.. warning::

    Every change of this file in the ``dev`` branch will lead to this ``N`` suffix to be reset to ``0``. Update this file only in the case when you're setting up the next release version!

.. _dev-release-any-branch:

Development releases from any branch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just like example above, but you want to make development releases
(prereleases) with a branch name  (``feature`` / ``bugfix`` / ``preview`` / ``beta`` / etc)
present in the version number.

For example, if the branch name is something like ``alpha``, ``beta``,
``preview`` or ``rc``, you can add ``{branch}`` substitution to template in your config file:

- ``setup.py``:

    .. code:: python

        setuptools.setup(
            ...,
            setuptools_git_versioning={
                "enabled": True,
                "version_file": VERSION_FILE,
                "count_commits_from_version_file": True,
                "dev_template": "{tag}.{branch}{ccount}",
                "dirty_template": "{tag}.{branch}{ccount}",
            },
        )

- ``pyproject.toml``:

    .. code:: toml

        [tool.setuptools-git-versioning]
        enabled = True
        version_file = "VERSION"
        count_commits_from_version_file = true
        dev_template = "{tag}.{branch}{ccount}"
        dirty_template = "{tag}.{branch}{ccount}"

Fourth commit to ``alpha`` branch with next release number ``1.2.3``
will generate a version number like ``1.2.3a4``.

Fifth commit to ``beta`` branch with next release number ``1.2.3``
will generate a version number like ``1.2.3b5``.

.. _dev-release-ignore-file:

Development releases using only branch name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is also possible to use branch names like ``1.0-alpha`` or ``1.1.beta``:

.. code:: python

    setuptools.setup(
        ...,
        setuptools_git_versioning={
            "enabled": True,
            "count_commits_from_version_file": True,
            "dev_template": "{branch}{ccount}",
            "dirty_template": "{branch}{ccount}",
            "version_file": VERSION_FILE,
        },
    )

.. code:: toml

    [tool.setuptools-git-versioning]
    enabled = true
    version_file = "VERSION"
    count_commits_from_version_file = true
    dev_template = "{branch}{ccount}"
    dirty_template = "{branch}{ccount}"

Second commit to ``1.0-alpha`` branch
will generate a version number like ``1.0a2``.

Third commit to ``1.2.beta`` branch
will generate a version number like ``1.2b3``.

If branch name is not :pep:`440` compliant, use :ref:`branch-formatter-option` option

.. note::

    Although ``VERSION`` file content is not used in this case, you still need to update it
    while changing your next release version.

    Otherwise this tool will not be able to properly calculate version number.
    The commits history is used for this calcucation,
    so no file changes means that ``ccount`` will not be reset to ``0``.

See also
""""""""
- :ref:`version-file-option` option
- :ref:`count-commits-option` option
- :ref:`dev-template-option` option
- :ref:`dirty-template-option` option
- :ref:`branch-formatter-option` option
