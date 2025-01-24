.. _target_plugin:

Targets plugins
=============================

*New in version 0.13.0*

What is a target?
------------------

A :class:`Target` is a Python class in earthkit-data that can write/add data
to a given location. There are several built-in :ref:`target <data-targets>`, the most
common being the :ref:`file <data-targets-file>` target.

Adding a new target as a pip plugin
-------------------------------------

A **targets plugin** is a Python package with a name that must start with ``earthkit-data-`` and consistently use "-" separators. Let us call it "earthkit-data-my-target". When it is hosted on PyPI we should be able to install it as:

.. code-block:: shell

    pip install earthkit-data-my-target


This package must contain a Python class inherited from :class:`earthkit.data.Target` to implement writing to a custom data target. Let us suppose the new class is called "MyClass". We should be able to import the class as:

.. code-block:: python

    from earthkit_data_my_target import MyClass

Please note that in the line above the package name has to contain "_" characters.

In the ``pyproject.toml`` file of the package the ``entry_points``
integration must be set as follow:

.. code-block:: toml

    entry-points."earthkit.data.targets".my-target = "earthkit_data_my_target:MyClass"


With this we could use the new target in :func:`to_target` as:

.. code-block:: python

    import earthkit.data

    ds = earthkit.data.to_target("my-target", ...)


.. note::

  The target name used in :func:`from_target` is only defined in the ``entry_points`` block in ``pyproject.toml``, so it is not deduced from the package name.


Example
-------

The ``earthkit-data-demo-target`` package demonstrates how to implement a ``targets plugin``. Its source code is located at https://github.com/ecmwf/earthkit-data-demo-target. This plugin enables earthkit-data to access data from an SQL database.

This demo package can be installed as:

.. code-block:: shell

  pip install earthkit-data-demo-target

Having finished the installation, tabular data can be read in earthkit-data as follows:

.. code-block:: python

    import earthkit.data

    # assume you have test.db available
    ds = earthkit.data.to_target(
        "demo-target",
        "sqlite:///test.db",
        "select * from data;",
        parse_dates=["time"],
    )
    df = ds.to_pandas()

The integration is performed by ``entry_points`` defined in  ``pyproject.toml``.

.. code-block:: toml

    entry-points."earthkit.data.targets".demo-target = "earthkit_data_demo_target:DemoTarget"


See the :ref:`/examples/demo_targets_plugin.ipynb` notebook for the full example.
