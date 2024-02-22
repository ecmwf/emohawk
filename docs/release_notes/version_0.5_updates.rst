Version 0.5 Updates
/////////////////////////


Version 0.5.2
===============

Fixes
++++++
- fixed issue when retrievals like :ref:`data-sources-mars` failed when a datelist with exactly five elements was used


Version 0.5.1
===============

New features
++++++++++++++++

- changed the default :ref:`cache policy <cache_policies>` to :ref:`off <off_cache_policy>`. See the :ref:`/examples/cache.ipynb` notebook example.
- enabled the :ref:`off <off_cache_policy>` cache policy to access remote sources like :ref:`data-sources-mars`
- allowed creating source :ref:`plugins <plugin-overview>`
- enabled reading :ref:`data-sources-url` sources as streams. See the :ref:`/examples/grib_url_stream.ipynb` notebook example
- enabled reading :ref:`data-sources-polytope` sources as streams
- added the :meth:`FieldList.to_fieldlist() <data.core.fieldlist.FieldList.to_fieldlist>` method to convert to a new :class:`FieldList` based on a given backend
- added the :meth:`nearest_point_haversine` and :meth:`nearest_point_kdtree` methods to find the nearest point out of a set of locations. See the :ref:`/examples/grib_nearest_gridpoint.ipynb` and :ref:`/examples/grib_time_series.ipynb` notebook examples.
- enabled using multiple keys and dictionaries in the :ref:`split_on <split_on>` request parameter for :ref:`data-sources-cds` retrievals
- enabled using list of requests in :ref:`data-sources-cds` retrievals
- added the experimental "constants" source type
- ensured consistent usage of ``pandas_read_csv_kwargs`` for :ref:`data-sources-file` and :ref:`data-sources-cds` sources
- added the ``bits_per_value`` option to :meth:`NumpyFieldList.save() <data.sources.numpy_list.NumpyFieldList.save>`
- when a :class:`~data.sources.numpy_list.NumpyFieldList` is written to disk with :meth:`NumpyFieldList.save() <data.sources.numpy_list.NumpyFieldList.save>` the ``generatingProcessIdentifier`` GRIB key is not set implicitly to 255 any longer. Instead, users must set its value when calling :meth:`Metadata.override() <data.core.metadata.Metadata.override>`.
- significantly reduced field size in a :class:`~data.sources.numpy_list.NumpyFieldList`. Available with ecCodes >= 2.34.0 and eccodes-python >= 1.17.0
- added experimental support for retrieving coverage json data from a :ref:`data-sources-polytope` source

Fixes
++++++
- fixed issue when slicing did not work on :class:`~data.core.fieldlist.FieldList` filtered with ``sel()``
- fixed crash in :meth:`FieldList.to_xarray() <data.core.fieldlist.FieldList.to_xarray>` when  the ``filter_by_keys`` option in ``backend_kwargs`` was used
- fixed issue when list of dates could not be used in a :ref:`data-sources-cds` request
- fixed issue when some metadata keys of a :class:`~data.sources.numpy_list.NumpyFieldList` did not match the actual field values. These metadata keys are now not available in a  :class:`~data.sources.numpy_list.NumpyFieldList`
- fixed issue when NetCDF input containing a coordinate with string values caused a crash
- ensured compatibility with the changes in ecCodes version 2.34.0.
