Welcome to earthkit-data's documentation
======================================================

.. warning::

    This project is **BETA** and will be **Experimental** for the foreseeable future. Interfaces and functionality are likely to change, and the project itself may be scrapped. **DO NOT** use this software in any project/software that is operational.

**earthkit-data** is a format-agnostic Python interface for geospatial data with a focus on meteorology and
climate science.

**earthkit-data** makes it simple to read, inspect and slice data from a wide range of
geospatial input types (:ref:`grib`, :ref:`netcdf` and more) and transform them into
familiar scientific Python objects (including numpy arrays, pandas dataframes, xarray datasets).

.. code-block:: python

    data = earthkit.data.from_source("file", "my-data.nc")
    arr = data.to_numpy()
    df = data.to_pandas()
    dataset = data.to_xarray()


**earthkit-data** provides additional convenient methods for quickly inspecting certain
features of your input data, such as data dimensionality, axes, coordinate
reference systems and bounding boxes.

.. toctree::
   :maxdepth: 1
   :caption: Examples
   :titlesonly:

   examples

.. toctree::
   :maxdepth: 1
   :caption: Documentation

   howtos
   guide/index
   api

.. toctree::
   :maxdepth: 1
   :caption: Installation

   install
   release_notes/index
   development
   licence


Indices and tables
==================

* :ref:`genindex`

.. * :ref:`modindex`
.. * :ref:`search`
