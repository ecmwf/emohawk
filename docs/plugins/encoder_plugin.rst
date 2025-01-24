.. _encoder_plugin:

Encoders plugins
=============================

*New in version 0.13.0*

What is an encoder?
-------------------

A :class:`Encoder` is a Python class in earthkit-data that can write/add data
to a given location. There are several built-in :ref:`encoder <data-encoders>`, the most
common being the :ref:`file <data-encoders-file>` encoder.

Adding a new encoder as a pip plugin
-------------------------------------

A **encoders plugin** is a Python package with a name that must start with ``earthkit-data-`` and consistently use "-" separators. Let us call it "earthkit-data-my-encoder". When it is hosted on PyPI we should be able to install it as:

.. code-block:: shell

    pip install earthkit-data-my-encoder


This package must contain a Python class inherited from :class:`earthkit.data.Encoder` to implement writing to a custom data target. Let us suppose the new class is called "MyClass". We should be able to import the class as:

.. code-block:: python

    from earthkit_data_my_encoder import MyClass

Please note that in the line above the package name has to contain "_" characters.

In the ``pyproject.toml`` file of the package the ``entry_points``
integration must be set as follow:

.. code-block:: toml

    entry-points."earthkit.data.encoders".my-encoder = "earthkit_data_my_encoder:MyClass"


With this we could use the new encoder in :func:`get_encoder` or :func:`to_target` as:

.. code-block:: python

    import earthkit.data

    encoder = earthkit.data.get_encoder("my-encoder", ...)
    ds = earthkit.data.to_target("file", encoder="my_encoder", ...)
    ds = earthkit.data.to_target("file", encoder=encoder, ...)


.. note::

  The encoder name used in the examples above is only defined in the ``entry_points`` block in ``pyproject.toml``, so it is not deduced from the package name.


Example
-------

The ``earthkit-data-demo-encoder`` package demonstrates how to implement a ``encoder plugin``. Its source code is located at https://github.com/ecmwf/earthkit-data-demo-encoder. This plugin enables earthkit-data to encode fields as a PNG.

This demo package can be installed as:

.. code-block:: shell

  pip install earthkit-data-demo-encoder

Having finished the installation, GRIB data can written to a PNG file asn follows:

.. code-block:: python

    import earthkit.data

    # get some GRIB data
    ds = earthkit.data.from_source("sample", "test.grib")

    # we write the first field into a PNG file
    ds[0].to_target("file", "_my_test.png", encoder="demo-encoder")


The integration is performed by ``entry_points`` defined in  ``pyproject.toml``.

.. code-block:: toml

    entry-points."earthkit.data.encoders".demo-encoder = "earthkit_data_demo_encoder:DemoEncoder"


See the :ref:`/examples/demo_encoders_plugin.ipynb` notebook for the full example.
