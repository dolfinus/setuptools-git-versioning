.. _tag_filter-option:

``tag_filter``
~~~~~~~~~~~~~~~~~~~~~

Callback to be used for filtering tag names before formatting and template
substitution.

.. note::

    This option is completely ignored if :ref:`version-file` schema is used.
    This is because all tags are set on ``master`` / ``main`` branch,
    so commits to other branches like ``develop`` are tagless.

.. note::

    This option is completely ignored if :ref:`version-callback` schema is used,
    because git commit history is not fetched in such a case.

Type
^^^^^
``str``

Default value
^^^^^^^^^^^^^
`None`

Usage
^^^^^^

Set when multiple products are tagged in a single repo.

If, for example, your repo has:

- `product_x/1.2.0`
- `product_x/1.2.1`
- `product_x/1.3.0`
- `product_y/2.0.0`
- `product_y/2.1.0`

and you only want versions from `product_y`, simply set:

.. code:: toml

    tag_filter = "product_y/.*"

This will limit the tags considered to those that start with `product_y`.

You will likely still need to construct a :ref:`tag-formatter-option` that
takes the entire tag into consideration.  This will be similar to the regexp
or function used by the tag_filter, but must return just the part of the tag
that is used for the version.

Possible values
^^^^^^^^^^^^^^^
- ``None``

    Disables this feature

- function full name in format ``"some.module:function_name"``

    Function should have signature ``(str) -> str``. It accepts original tag name and returns
    the tag name if it should be in the list and None if it is to be filtered out.

    .. warning::

        Exception will be raised if module or function/lambda is missing or has invalid signature

- regexp like ``"tag-prefix/.*"``

    .. warning::

        Exception will be raised if regexp is invalid

    .. warning::

        If regexp doesn't match any tag, the filter will return the empty list, and
        the default "0.0.1" version will be selected.