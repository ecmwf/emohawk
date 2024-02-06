.. _parts:

Using parts for file and url sources
====================================

For the :ref:`data-sources-file` and :ref:`data-sources-url` sources we can specify the parts (byte ranges) we want to read from the given input.

A **single part** is a pair (list or tuple) in the following format::

    (offset, length)

where:

    - offset: the start byte position
    - length: the number of bytes to be read from the offset

**Multiple parts** can be defined as a list or tuple of single parts. These have to be specified in an ascending offset order, no overlapping is allowed.


Using the parts kwarg
----------------------

For both sources we can use the ``parts`` kwarg to define the parts for all the ``path``\s or ``urls``\ s. A few examples:

.. code-block:: python

    # file
    ds = earthkit.data.from_source("file", "my.grib", parts=(0, 150))
    ds = earthkit.data.from_source("file", "my.grib", parts=[(0, 150), (400, 160)])

    # url
    ds = earthkit.data.from_source("url", "http://my-host/my.grib", parts=(0, 150))
    ds = earthkit.data.from_source(
        "url", "http://my-host/my.grib", parts=[(0, 150), (400, 160)]
    )


Specifying the parts for each file
-------------------------------------

If we have multiple paths/urls and want to specify different parts for each we need to add the parts to the  ``path`` or ``urls`` arguments.

.. code-block:: python

    # file
    ds = earthkit.data.from_source(
        "file",
        [
            ("a.grib", (0, 150)),
            ("b.grib", (240, 120)),
            ("c.grib", None),
            ("d.grib", [(240, 120), (720, 120)]),
        ],
    )

When we use this mode the ``parts`` kwarg cannot be used!

Examples:

    - :ref:`/examples/grib_file_parts.ipynb`
