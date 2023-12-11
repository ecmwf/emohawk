.. _sources_plugin:

Sources plugins
=============================

What is a source?
------------------

A :class:`Source` is a Python class in earthkit-data that can access data
from a given location or provider. There are several built-in :ref:`sources <data-sources>`, the most
common being the :ref:`file <data-sources-file>` source.

Adding a new source as a pip plugin
-------------------------------------

A **sources plugin** should contain a Python class inherited from :class:`earthkit.data.Source` to implement access for a custom data source. Let us suppose the new class is called "MyClass".

The name of the Python package containing the plugin should start with ``earthkit-data-`` and use "-". Let us call it "earthkit-data-my-source". When it is hosted on PyPI we should be able to install this package as:

.. code-block:: shell

    pip install earthkit-data-my-source

The package to import should start with :py:class:`earthkit_data\_` and use "_". In our case this would be: "earthkit_data_my_source". We should be able to import the class from it as:

.. code-block:: python

    from earthkit_data_my_source import MyClass

In the ``setup.cfg`` file of the package the ``entry_points``
integration must be set as follow:

.. code-block:: ini

    [options.entry_points]
    earthkit.data.sources =
        my-source = earthkit_data_my_source:MyClass


With this we could use the new source in :func:`from_source` as:

.. code-block:: python

    import earthkit.data

    ds = earthkit.data.from_source("my-source", ...)


.. note::

  The source name used in :func:`from_source` is only defined in the ``entry_points`` block in ``setup.cfg``, so it is not deduced from the package name.


Example
-------

The ``earthkit-data-demo-source`` package demonstrates how to implement a ``sources plugin``. Its source code is located at https://github.com/ecmwf/earthkit-data-demo-source. This plugin enables earthkit-data to access data from an SQL database.

This demo package is not hosted on PyPI but we need to install it from github:

.. code-block:: shell

  pip install git+https://github.com/ecmwf/earthkit-data-demo-source

Having finished the installation, tabular data can be read in earthkit-data as follows:

.. code-block:: python

    import earthkit.data

    ds = earthkit.data.from_source(
        "demo-source",
        "sqlite:///test.db",
        "select * from data;",
        parse_dates=["time"],
    )
    df = ds.to_pandas()

The integration is performed by ``entry_points`` is defined in  ``setup.cfg``.

.. code-block:: ini

    [options.entry_points]
    earthkit.data.sources =
        demo-source = earthkit_data_demo_source:DemoSource


See the :ref:`/examples/demo_sources_plugin.ipynb` notebook for the full example.
