.. _plugins-reference:

The plugin mechanism
===============================

This document discusses how plugins are integrated into earthkit-data.


Plugin as python packages using ``entry_points``
------------------------------------------------

A plugin can be added to earthkit-data by using the standard `Python plugin <https://packaging.python.org/guides/creating-and-discovering-plugins>`_ mechanism based on ``entry_points``.

This requires the plugin package to have a special section in its ``setup.cfg`` file. During the installation of the package, the plugin registers itself thanks to the entry points in it configuration, making earthkit-data aware of the new capabilities.
Then, the user can take advantage of the shared code through the enhanced :py:func:`from_source` etc. methods.

The following example shows how it can be done.

:Example:

    Let us suppose our package is called **earthkit-data-package-name** and implements a ``"sources"``  (note the plural form) plugin type . If it is  a ``pip`` package using ``setuptools`` we need to add an ``entry_points`` block to ``setup.cfg``:

    .. code-block:: ini

        [options.entry_points]
        earthkit.data.sources =
            foo = earthkit_data_package_name:FooClass
            bar = earthkit_data_package_name:BarClass

    This block specifies that in the package the :py:class:`FooClass` class implements the ``"foo"`` source, while
    the :py:class:`BarClass` class implements the ``"bar"`` source. In earthkit-data we will be able to use them as:

    .. code-block:: python

        from earthkit.data import from_source

        ds1 = from_source("foo", args1)
        ds2 = from_source("bar", args2)



See the individual documentation for each plugin type for detailed examples and
the standard `Python plugin documentation <https://packaging.python.org/guides/creating-and-discovering-plugins>`_.
