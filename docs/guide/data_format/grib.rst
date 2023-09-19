.. _grib:


GRIB
---------

GRIB is the WMO's format for binary gridded data consisting of GRIB messages, which in the earthkit terminology are called **fields**. The earthkit-data GRIB interface is based on :xref:`eccodes` and can handle both GRIB `edition 1 <https://community.wmo.int/activity-areas/wmo-codes/manual-codes/grib-edition-1>`_ and `edition 2 <https://library.wmo.int/index.php?lvl=notice_display&id=10684>`_.

Fieldlists
+++++++++++

We can read/retrieve GRIB data with :func:`from_source`. The resulting object will be a :class:`~data.readers.grib.index.GribFieldList` representing a list of :class:`~data.readers.grib.codes.GribField`\ s, which we can iterate through:

.. code-block:: python

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")

    >>> len(ds)
    2

    >>> for f in ds:
    ...     print(f)
    ...
    GribField(2t,1000,20200513,1200,0,0)
    GribField(msl,1000,20200513,1200,0,0)


The following table gives us an overview of the GRIB :class:`~data.readers.grib.index.FieldList` API:

.. list-table:: Highlights of the GRIB FieldList API
   :header-rows: 1

   * - Methods/Operators
     - API
   * - :ref:`conversion`
     - :meth:`~data.readers.grib.index.GribFieldList.to_xarray`
   * - :ref:`concat`
     -
   * - :ref:`iter`
     -
   * - :ref:`slice`
     -
   * - :ref:`sel`
     - :meth:`~data.readers.grib.index.GribFieldList.sel`
   * - :ref:`order_by`
     - :meth:`~data.readers.grib.index.GribFieldList.order_by`
   * - :ref:`data_values`
     - :meth:`~data.readers.grib.index.GribFieldList.to_numpy`
   * - :ref:`metadata`
     - :meth:`~data.readers.grib.index.GribFieldList.metadata`
   * - :ref:`inspection`
     - :meth:`~data.readers.grib.index.GribFieldList.ls`, :meth:`~data.readers.grib.index.GribFieldList.head` and :meth:`~data.readers.grib.index.GribFieldList.tail`

Fields
+++++++

A :class:`~data.readers.grib.codes.GribField` represent a single GRIB field. It primarily offers methods to:

 - :ref:`extract field values <data_values>`, such as :meth:`~data.readers.grib.codes.GribField.to_numpy`
 - :ref:`extract field metadata <metadata>`, such as :meth:`~data.readers.grib.codes.GribField.metadata`

Examples:

    - :ref:`/examples/grib_overview.ipynb`
    - :ref:`/examples/grib_metadata.ipynb`
    - :ref:`/examples/grib_selection.ipynb`
    - :ref:`/examples/grib_missing.ipynb`
