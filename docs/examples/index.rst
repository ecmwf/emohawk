.. _examples:

Examples
============

Here is a list of example notebooks to illustrate how to use earthkit-data.

Data sources
++++++++++++++

.. toctree::
    :maxdepth: 1

    files.ipynb
    multi_files.ipynb
    file_parts.ipynb
    file_stream.ipynb
    tar_files.ipynb
    data_from_stream.ipynb
    url.ipynb
    url_parts.ipynb
    url_stream.ipynb
    netcdf_opendap.ipynb
    mars.ipynb
    ads.ipynb
    cds.ipynb
    ecmwf_open_data.ipynb
    fdb.ipynb
    polytope.ipynb
    polytope_feature.ipynb
    s3.ipynb
    wekeo.ipynb

GRIB
++++++

.. toctree::
    :maxdepth: 1

    grib_overview.ipynb
    grib_metadata.ipynb
    grib_lat_lon_value.ipynb
    grib_selection.ipynb
    grib_indexing.ipynb
    grib_missing.ipynb
    grib_metadata_object.ipynb
    grib_modification.ipynb
    numpy_fieldlist.ipynb
    grib_array_backends.ipynb
    grib_nearest_gridpoint.ipynb
    grib_time_series.ipynb
    grib_fdb_write.ipynb
    grib_to_netcdf.ipynb


NetCDF
++++++

.. toctree::
    :maxdepth: 1
    :glob:

    netcdf.ipynb
    netcdf_fieldlist.ipynb


BUFR
++++++

.. toctree::
    :maxdepth: 1
    :glob:

    bufr*

ODB
++++++

.. toctree::
    :maxdepth: 1
    :glob:

    odb*

CoverageJSON
+++++++++++++

.. toctree::
    :maxdepth: 1
    :glob:

    polytope_time_series.ipynb
    polytope_polygon_coverage.ipynb
    polytope_vertical_profile.ipynb

GeoTIFF
+++++++++++++

.. toctree::
    :maxdepth: 1
    :glob:

    geotiff.ipynb

GeoJSON/GeoPandas
+++++++++++++++++++++++++++++

.. toctree::
    :maxdepth: 1
    :glob:

    geojson_geopandas.ipynb

Shapefile
+++++++++++++++++++++++++++++

.. toctree::
    :maxdepth: 1
    :glob:

    shapefile.ipynb

.. _examples_lod:

Dictionary input
++++++++++++++++++++++

.. toctree::
    :maxdepth: 1
    :glob:

    fields_from_dict_in_loop.ipynb
    list_of_dicts_overview
    list_of_dicts_geography


Other inputs
+++++++++++++

.. toctree::
    :maxdepth: 1
    :glob:

    from_object.ipynb
    pandas.ipynb


.. _examples_xr_engine:

Xarray engine
+++++++++++++

.. toctree::
    :maxdepth: 1
    :glob:

    xarray_engine_overview.ipynb
    xarray_engine_temporal.ipynb
    xarray_engine_level.ipynb
    xarray_engine_variable_key.ipynb
    xarray_engine_field_dims.ipynb
    xarray_engine_to_grib.ipynb
    xarray_engine_split.ipynb
    xarray_engine_seasonal.ipynb

Targets and encoders
+++++++++++++++++++++

.. toctree::
    :maxdepth: 1
    :glob:

    grib_to_file_target.ipynb
    grib_to_fdb_target.ipynb
    grib_encoder.ipynb

Miscellaneous
+++++++++++++

.. toctree::
    :maxdepth: 1
    :glob:

    config.ipynb
    config_env_vars.ipynb
    cache.ipynb
    projection.ipynb
    metadata.ipynb
    demo_sources_plugin.ipynb
