Version 0.4 Updates
/////////////////////////

.. warning::
    This is an upcoming release.

Version 0.4.0
===============

New features
++++++++++++++++

- added new sources :ref:`data-sources-wekeo` and :ref:`data-sources-wekeocds` to retrieve data from `WEkEO <https://www.wekeo.eu/>`_. See the :ref:`/examples/wekeo.ipynb` notebook example.
- added the ``append`` option to :meth:`FieldList.save() <data.core.fieldlist.FieldList.save>`.
- added the ``dtype`` option to the ``to_data()``, ``to_latlon()`` and ``to_points()`` methods both on a :class:`~data.core.fieldlist.Field` or :class:`~data.core.fieldlist.FieldList`.
- allowed access to 32-bit GRIB data values without requiring a cast in Python from 64 to 32 bits. Only works with a recent ecCodes version (ecCodes >= 2.31.0 and eccodes-python >= 1.6.0 required). In order to use this feature set ``dtype=np.float32`` in the ``to_numpy()``, ``to_data()``, ``to_latlon()`` or ``to_points()`` methods on either a :class:`~data.core.fieldlist.Field` or :class:`~data.core.fieldlist.FieldList`.
- added :meth:`~data.core.readers.csv.CSVReader.to_xarray` to csv data
- no ecCodes installation is required when only accessing non-GRIB data


Fixes
++++++

- fixed issue when concatenation for :class:`~data.core.readers.numpy_list.NumpyFieldList` did not work
- fixed issue when concatenation to an empty Fieldlist did not work
- fixed issue when could not get values from a  :class:`~data.core.readers.numpy_list.NumpyFieldList`
- fixed issue when could not retrieve data from the :ref:`CDS <data-sources-wekeo>` beacause the ``month`` and ``day`` request parameters were pre-filled by earthkit-data. These parameters are not pre-filled now.
- fixed issue when missing values were not correctly written to GRIB output
- fixed issue when could not read non-fieldlist type NetCDF data with :func:`from_source`
