Comparison with other tools
===========================

Alternatives
------------
- `setuptools-scm <https://github.com/pypa/setuptools_scm>`_
- `versioneer <https://github.com/python-versioneer/python-versioneer>`_
- `versioningit <https://github.com/jwodder/versioningit>`_
- `dunamai <https://github.com/mtkennerly/dunamai>`_
- `miniver <https://github.com/jbweston/miniver>`_
- `setuptools-git-ver <https://github.com/camas/setuptools-git-ver>`_ (Base package)

General information
-------------------

+---------------------------+-----------------+----------------+--------------------+
| Package                   | Latest release  | License        | PEP 440 compatible |
+===========================+=================+================+====================+
| setuptools-git-versioning |            2025 | MIT            |        yes         |
+---------------------------+-----------------+----------------+--------------------+
| setuptools-scm            |            2023 | MIT            |        yes         |
+---------------------------+-----------------+----------------+--------------------+
| versioneer                |            2023 | Public domain  |        yes         |
+---------------------------+-----------------+----------------+--------------------+
| versioningit              |            2024 | MIT            |        yes         |
+---------------------------+-----------------+----------------+--------------------+
| dunamai                   |            2024 | MIT            |        yes         |
+---------------------------+-----------------+----------------+--------------------+
| miniver                   |            2021 | Public domain  |         no         |
+---------------------------+-----------------+----------------+--------------------+
| setuptools-git-ver        |            2019 | MIT            |         no         |
+---------------------------+-----------------+----------------+--------------------+

VCS support
-------------------

+---------------------------+-----+-----------+-------------------------------+
| Package                   | Git | Mercurial | Can be used in git submodules |
+===========================+=====+===========+===============================+
| setuptools-git-versioning | yes |     no    |             yes               |
+---------------------------+-----+-----------+-------------------------------+
| setuptools-scm            | yes |    yes    |             yes               |
+---------------------------+-----+-----------+-------------------------------+
| versioneer                | yes |     no    |              no               |
+---------------------------+-----+-----------+-------------------------------+
| versioningit              | yes |    yes    |              no               |
+---------------------------+-----+-----------+-------------------------------+
| dunamai                   | yes |    yes    |              no               |
+---------------------------+-----+-----------+-------------------------------+
| miniver                   | yes |     no    |              no               |
+---------------------------+-----+-----------+-------------------------------+
| setuptools-git-ver        | yes |     no    |              no               |
+---------------------------+-----+-----------+-------------------------------+

Development
------------

+----------------------------+---------------+-------+-----------+-------+------------+
| Package                    | Documentation | Tests | Changelog | CI/CD | pre-commit |
+============================+===============+=======+===========+=======+============+
| setuptools-git-versioning  |      site     |  yes  |    yes    |  yes  |    yes     |
+----------------------------+---------------+-------+-----------+-------+------------+
| setuptools-scm             |      site     |  yes  |    yes    |  yes  |    yes     |
+----------------------------+---------------+-------+-----------+-------+------------+
| versioneer                 |      repo     |  yes  |    yes    |  yes  |     no     |
+----------------------------+---------------+-------+-----------+-------+------------+
| versioningit               |      site     |  yes  |    yes    |  yes  |    yes     |
+----------------------------+---------------+-------+-----------+-------+------------+
| dunamai                    |      site     |  yes  |    yes    |  yes  |    yes     |
+----------------------------+---------------+-------+-----------+-------+------------+
| miniver                    |     readme    |  yes  |    yes    |  yes  |     no     |
+----------------------------+---------------+-------+-----------+-------+------------+
| setuptools-git-ver         |     readme    |   no  |     no    |   no  |     no     |
+----------------------------+---------------+-------+-----------+-------+------------+

Python version support
----------------------

+---------------------------+----------------+------------+--------------+
| Package                   | Python support | Type hints | PyPy support |
+===========================+================+============+==============+
| setuptools-git-versioning |           3.7+ |    yes     |     yes      |
+---------------------------+----------------+------------+--------------+
| setuptools-scm            |           3.7+ |    yes     |   unknown    |
+---------------------------+----------------+------------+--------------+
| versioneer                |           3.7+ |     no     |   unknown    |
+---------------------------+----------------+------------+--------------+
| versioningit              |           3.6+ |    yes     |     yes      |
+---------------------------+----------------+------------+--------------+
| dunamai                   |           3.5+ |    yes     |   unknown    |
+---------------------------+----------------+------------+--------------+
| miniver                   |           3.5+ |     no     |   unknown    |
+---------------------------+----------------+------------+--------------+
| setuptools-git-ver        |           3.7+ |     no     |   unknown    |
+---------------------------+----------------+------------+--------------+

OS support
-----------

+---------------------------+-------+-------+---------+
| Package                   | Linux | MacOS | Windows |
+===========================+=======+=======+=========+
| setuptools-git-versioning |  yes  |  yes  |   yes   |
+---------------------------+-------+-------+---------+
| setuptools-scm            |  yes  |  yes  |   yes   |
+---------------------------+-------+-------+---------+
| versioneer                |  yes  |  yes  |   yes   |
+---------------------------+-------+-------+---------+
| versioningit              |  yes  |  yes  |   yes   |
+---------------------------+-------+-------+---------+
| dunamai                   |  yes  |  yes  |   yes   |
+---------------------------+-------+-------+---------+
| miniver                   |  yes  |  yes  |   yes   |
+---------------------------+-------+-------+---------+
| setuptools-git-ver        |  yes  |  yes  |   yes   |
+---------------------------+-------+-------+---------+

Configuration
-------------------

+---------------------------+----------------+------------+------------+
| Package                   | pyproject.toml |  setup.py  | setup.cfg  |
+===========================+================+============+============+
| setuptools-git-versioning |       yes      |     yes    |     no     |
+---------------------------+----------------+------------+------------+
| setuptools-scm            |       yes      | deprecated | deprecated |
+---------------------------+----------------+------------+------------+
| versioneer                |        no      | deprecated |    yes     |
+---------------------------+----------------+------------+------------+
| versioningit              |       yes      |     yes    |     no     |
+---------------------------+----------------+------------+------------+
| dunamai                   |       yes      |     yes    |     no     |
+---------------------------+----------------+------------+------------+
| miniver                   |        no      |     yes    |     no     |
+---------------------------+----------------+------------+------------+
| setuptools-git-ver        |        no      |     yes    |     no     |
+---------------------------+----------------+------------+------------+

:ref:`Substitutions <substitutions>`
------------------------------------

+---------------------------+---------------+-----------+----------+
| Package                   | Commits count | Short SHA | Full SHA |
+===========================+===============+===========+==========+
| setuptools-git-versioning |     yes       |    yes    |   yes    |
+---------------------------+---------------+-----------+----------+
| setuptools-scm            |     yes       |    yes    |    no    |
+---------------------------+---------------+-----------+----------+
| versioneer                |     yes       |    yes    |   yes    |
+---------------------------+---------------+-----------+----------+
| versioningit              |     yes       |    yes    |   yes    |
+---------------------------+---------------+-----------+----------+
| dunamai                   |     yes       |    yes    |   yes    |
+---------------------------+---------------+-----------+----------+
| miniver                   |     yes       |    yes    |    no    |
+---------------------------+---------------+-----------+----------+
| setuptools-git-ver        |     yes       |    yes    |    no    |
+---------------------------+---------------+-----------+----------+

+---------------------------+--------+--------------------+
| Package                   | Branch | Branch name escape |
+===========================+========+====================+
| setuptools-git-versioning |  yes   |        yes         |
+---------------------------+--------+--------------------+
| setuptools-scm            |   no   |         no         |
+---------------------------+--------+--------------------+
| versioneer                |   no   |         no         |
+---------------------------+--------+--------------------+
| versioningit              |  yes   |         no         |
+---------------------------+--------+--------------------+
| dunamai                   |  yes   |        yes         |
+---------------------------+--------+--------------------+
| miniver                   |   no   |         no         |
+---------------------------+--------+--------------------+
| setuptools-git-ver        |   no   |         no         |
+---------------------------+--------+--------------------+

+---------------------------+---------------+------------------+-------------------+--------------+
| Package                   | Tag timestamp | Commit timestamp | Current timestamp | Env variable |
+===========================+===============+==================+===================+==============+
| setuptools-git-versioning |       no      |        no        |        yes        |     yes      |
+---------------------------+---------------+------------------+-------------------+--------------+
| setuptools-scm            |       no      |        no        |         no        |      no      |
+---------------------------+---------------+------------------+-------------------+--------------+
| versioneer                |       no      |        no        |         no        |      no      |
+---------------------------+---------------+------------------+-------------------+--------------+
| versioningit              |      yes      |       yes        |        yes        |      no      |
+---------------------------+---------------+------------------+-------------------+--------------+
| dunamai                   |      no       |       yes        |         no        |      no      |
+---------------------------+---------------+------------------+-------------------+--------------+
| miniver                   |       no      |        no        |         no        |      no      |
+---------------------------+---------------+------------------+-------------------+--------------+
| setuptools-git-ver        |       no      |        no        |         no        |      no      |
+---------------------------+---------------+------------------+-------------------+--------------+

:ref:`Tag-based versioning <tag-based-release>`
-----------------------------------------------

+---------------------------+-------------------------+---------------+-----------------+
| Package                   | Post (distance) version | Dirty version | Initial version |
+===========================+=========================+===============+=================+
| setuptools-git-versioning |           yes           |      yes      |       yes       |
+---------------------------+-------------------------+---------------+-----------------+
| setuptools-scm            |           yes           |      yes      |        no       |
+---------------------------+-------------------------+---------------+-----------------+
| versioneer                |           yes           |       no      |        no       |
+---------------------------+-------------------------+---------------+-----------------+
| versioningit              |           yes           |      yes      |       yes       |
+---------------------------+-------------------------+---------------+-----------------+
| dunamai                   |           yes           |      yes      |        no       |
+---------------------------+-------------------------+---------------+-----------------+
| miniver                   |            no           |       no      |        no       |
+---------------------------+-------------------------+---------------+-----------------+
| setuptools-git-ver        |           yes           |      yes      |        no       |
+---------------------------+-------------------------+---------------+-----------------+


+---------------------------+-------------------+-------------------+------------------------------------+
| Package                   | Remove tag prefix | Remove tag suffix | Select only tags matching template |
+===========================+===================+===================+====================================+
| setuptools-git-versioning |        yes        |        yes        |                yes                 |
+---------------------------+-------------------+-------------------+------------------------------------+
| setuptools-scm            |         no        |         no        |                 no                 |
+---------------------------+-------------------+-------------------+------------------------------------+
| versioneer                |         no        |         no        |                 no                 |
+---------------------------+-------------------+-------------------+------------------------------------+
| versioningit              |        yes        |        yes        |                yes                 |
+---------------------------+-------------------+-------------------+------------------------------------+
| dunamai                   |         no        |         no        |                yes                 |
+---------------------------+-------------------+-------------------+------------------------------------+
| miniver                   |         no        |         no        |                 no                 |
+---------------------------+-------------------+-------------------+------------------------------------+
| setuptools-git-ver        |         no        |         no        |                 no                 |
+---------------------------+-------------------+-------------------+------------------------------------+

:ref:`File-based versioning <file-based-release>`
-------------------------------------------------

+---------------------------+----------------+----------------------------------------+-------------------------+
| Package                   | Read from file |             Write to file              | Use file commit history |
+===========================+================+========================================+=========================+
| setuptools-git-versioning |       yes      | no (but can be done using bash script) |          yes            |
+---------------------------+----------------+----------------------------------------+-------------------------+
| setuptools-scm            |        no      |                  yes                   |           no            |
+---------------------------+----------------+----------------------------------------+-------------------------+
| versioneer                |       yes      |                  yes                   |           no            |
+---------------------------+----------------+----------------------------------------+-------------------------+
| versioningit              |        no      |                  yes                   |           no            |
+---------------------------+----------------+----------------------------------------+-------------------------+
| dunamai                   |        no      | no (but can be done using bash script) |           no            |
+---------------------------+----------------+----------------------------------------+-------------------------+
| miniver                   |        no      |                  yes                   |           no            |
+---------------------------+----------------+----------------------------------------+-------------------------+
| setuptools-git-ver        |        no      |                   no                   |           no            |
+---------------------------+----------------+----------------------------------------+-------------------------+

:ref:`Callback-based versioning <callback-based-release>`
---------------------------------------------------------

+---------------------------+---------------------------------------------+---------------------------------------+
| Package                   | Use callback function to get version number | Use module variable as version number |
+===========================+=============================================+=======================================+
| setuptools-git-versioning |                     yes                     |                  yes                  |
+---------------------------+---------------------------------------------+---------------------------------------+
| setuptools-scm            |                      no                     |                   no                  |
+---------------------------+---------------------------------------------+---------------------------------------+
| versioneer                |                      no                     |                   no                  |
+---------------------------+---------------------------------------------+---------------------------------------+
| versioningit              |                     yes                     |                   no                  |
+---------------------------+---------------------------------------------+---------------------------------------+
| dunamai                   |                      no                     |                   no                  |
+---------------------------+---------------------------------------------+---------------------------------------+
| miniver                   |                      no                     |                   no                  |
+---------------------------+---------------------------------------------+---------------------------------------+
| setuptools-git-ver        |                      no                     |                   no                  |
+---------------------------+---------------------------------------------+---------------------------------------+

Misc
----

+---------------------------+------------------------------+---------------------+
| Package                   | Reuse functions in your code | Supports extensions |
+===========================+==============================+=====================+
| setuptools-git-versioning |              yes             |          no         |
+---------------------------+------------------------------+---------------------+
| setuptools-scm            |              yes             |          no         |
+---------------------------+------------------------------+---------------------+
| versioneer                |              yes             |          no         |
+---------------------------+------------------------------+---------------------+
| versioningit              |              yes             |         yes         |
+---------------------------+------------------------------+---------------------+
| dunamai                   |              yes             |          no         |
+---------------------------+------------------------------+---------------------+
| miniver                   |              yes             |          no         |
+---------------------------+------------------------------+---------------------+
| setuptools-git-ver        |               no             |          no         |
+---------------------------+------------------------------+---------------------+
