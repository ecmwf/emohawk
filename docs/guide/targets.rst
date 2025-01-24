.. _data-targets:

Targets
===============

A **target** can represent a file, a database, a remote server etc. Data is written/added to a target by using a suitable :ref:`encoder <data-encoders>`.

Writing data to a target
----------------------------

There are three different ways to write/add data to a given target:

  - using :func:`to_target` on a data object
  - using the standalone :func:`to_target` method
  - using a :py:class:`Target` object

.. code-block:: python

    import earthkit.data

    # read GRIB data into a fieldlist
    ds = earthkit.data.from_source("file", "docs/examples/test.grib")

    # write the fieldlist to a file in different ways

    # Method 1: using to_target() on the data object
    ds.to_target("file", "_my_res_1.grib")

    # Method 2: using the standalone to_target() method
    from earthkit.data import to_target

    to_target("file", "_my_res_2.grib", data=ds)

    # Method 3: using a target object
    from earthkit.data import get_target

    with get_target("file", "_my_res_3.grib") as t:
        t.write(ds)

    # Method 4: using a target object
    from earthkit.data.targets.file import FileTarget

    with FileTarget("_my_res_4.grib") as t:
        t.write(ds)


Examples:

  - :ref:`/examples/grib_to_file_target.ipynb`
  - :ref:`/examples/grib_to_fdb_target.ipynb`

to_target()
---------------------------

We can write data to a given target by using :func:`to_target`. It can be either invoked on a data object or the data object can be specified as ``data``.

.. py:function:: to_target(name, *args, data=None, **kwargs)

  Write data :ref:`data object <data-object>` to the target specified by ``name`` .

  :param str name: the target (see below)
  :param tuple *args: specify target parameters
  :param data: specify the data to write. Cannot be set when :func:`to_target` is called on a data object.
  :param dict **kwargs: specify additional target parameters. Also specify the encoder parameters.


Built in targets
---------------------

**earthkit-data** has the following built-in targets:

  .. list-table:: Data targets
    :widths: 20 60 20
    :header-rows: 1

    * - Name
      - Description
      - Class
    * - :ref:`data-targets-file`
      - write data to a file/files
      - :py:class:`FileTarget`
    * - :ref:`data-targets-fdb`
      - add data to a `Fields DataBase <https://fields-database.readthedocs.io/en/latest/>`_ (FDB)
      - :py:class:`FDBTarget`
    * - :ref:`data-targets-multio`
      - add data to Multio
      - :py:class:`MultioTarget`

----------------------------------





.. _data-targets-file:

file
----

.. py:function:: to_target("file", file, split_output=False, append=False, data=None, encoder=None, template=None, metadata=None, **kwargs)
  :noindex:

  The simplest target is ``file``, which can access a local file/list of files.

  :param file: The file path or file-like object to write to.
  :type file: str or file-like object
  :param bool split_output: If True, the output file name defines a pattern containing metadata keys in the format of ``{key}``. Each data item (e.g. a field) will be written into a file with a name created by substituting the relevant metadata values in the filename pattern. E.g. ``"{param}_{level}_{typeOfLevel}.grib"``. Only used if ``file`` is a path.
  :param bool append:  If True, the file is opened in append mode. Only used if ``file`` is a path.
  :param data: specify the data to write. Cannot be set when :func:`to_target` is called on a data object.
  :param encoder: The encoder to use to encode the data. When it is a str, the encoder is looked up in
    the available :ref:`data-encoders`. When None, the encoder type will be determined from the data
    to write (if possible) or from the :class:`Target` properties. When a suitable encoder cannot be instantiated raises
    ValueError.
  :type encoder: str, :py:class:`Encoder`, None
  :param template: The template to be used by the encoder.
  :type template: obj, None
  :param dict **kwargs: other keyword arguments passed to the encoder



.. _data-targets-fdb:

fdb
----

.. py:function:: to_target("fdb", fdb=None, config=None, userconfig=None, data=None, encoder=None, template=None, metadata=None, **kwargs)
  :noindex:

  The ``fdb`` target writes to an `FDB (Fields DataBase) <https://fields-database.readthedocs.io/en/latest/>`_, which is a domain-specific object store developed at ECMWF for storing, indexing and retrieving GRIB data. earthkit-data uses the `pyfdb <https://pyfdb.readthedocs.io/en/latest>`_ package to add data to FDB.

  :param fdb: the FDB to write to
  :type fdb: pyfdb.FDB, None
  :param dict,str config: the FDB configuration directly passed to ``pyfdb.FDB()``. If not provided, the configuration is either read from the environment or the default configuration is used. Only used if no ``fdb`` is specified.
  :param dict,str userconfig: the FDB user configuration directly passed to ``pyfdb.FDB()``. If not provided, the configuration is either read from the environment or the default configuration is used. Only used if no ``fdb`` is specified.
  :param data: specify the data to write. Cannot be set when :func:`to_target` is called on a data object.
  :param encoder: The encoder to use to encode the data. When it is a str, the encoder is looked up in
    the available :ref:`data-encoders`. When None, the encoder type will be determined from the data
    to write (if possible) or from the :class:`Target` properties. When a suitable encoder cannot be instantiated raises
    ValueError.
  :type encoder: str, :py:class:`Encoder`, None
  :param template: The template to be used by the encoder.
  :type template: obj, None
  :param dict **kwargs: other keyword arguments passed to the encoder


.. _data-targets-multio:

multio
------

.. py:function:: to_target("multio", plan=None, data=None, template=None, metadata=None, **kwargs)
  :noindex:

  :param plan:  Multio plan
  :type plan: Client, os.PathLike, str, dict
  :param data: specify the data to write. Cannot be set when :func:`to_target` is called on a data object.
  :param template: The template to be used by the encoder.
  :type template: obj, None
  :param dict **kwargs: other keyword arguments passed to the encoder
