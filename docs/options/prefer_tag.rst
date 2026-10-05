.. _prefer-tag-option:

``prefer_tag``
~~~~~~~~~~~~~~

Used together with the :ref:`version-file-option` option.

By default, when :ref:`version-file-option` is set, any tags in the repo are
ignored (see :github:issue:`155`). With this option enabled, the latest Git tag takes precedence over the version file content.

.. note::

    This option is used only with :ref:`version-file-option`,
    and only takes effect when the repo actually contains at least one tag;
    otherwise the version file content is used as usual.

When the tag and the version file content are different,
a warning is logged, so stale version files are easier to notice.

Type
^^^^
``bool``

Default value
^^^^^^^^^^^^^
``False``
