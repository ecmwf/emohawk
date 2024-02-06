.. _split_on:

Using split_on in CDS retrievals
====================================

A :ref:`data-sources-cds` request can contain the ``split_on`` parameter. It does not specify the data but instructs :ref:`from_source <data-sources-cds>` to split the request into multiple parts, which are then executed independently and the resulting data will be stored in different files. However, the actual storage is hidden from the users and they can still work with the results as a single object.

Single key
-----------

``split_on`` can be a single string referring to the key the request should be split on:

  .. code-block:: python

      import earthkit.data

      ds = earthkit.data.from_source(
          "cds",
          "reanalysis-era5-single-levels",
          variable=["2t", "msl"],
          product_type="reanalysis",
          area=[50, -10, 40, 10],  # N,W,S,E
          grid=[2, 2],
          date="2012-05-10",
          time=[0, 12],
          split_on="variable",
      )

This will send 2 requests to the CDS one for "2t" and another one for "msl".

Sequence of keys
-----------------

A sequence of keys can also be specified:

  .. code-block:: python

      import earthkit.data

      ds = earthkit.data.from_source(
          "cds",
          "reanalysis-era5-single-levels",
          variable=["2t", "msl"],
          product_type="reanalysis",
          area=[50, -10, 40, 10],  # N,W,S,E
          grid=[2, 2],
          date="2012-05-10",
          time=[0, 12],
          split_on=("variable", "time"),
      )

This will send 4 requests to the CDS:

    - variable="2t",  time=0
    - variable="2t",  time=12
    - variable="msl", time=0
    - variable="msl", time=12

Dictionary of keys
----------------------

By specifying a dict we can define grouping per key for the splitting:

  .. code-block:: python

      import earthkit.data

      ds = earthkit.data.from_source(
          "cds",
          "reanalysis-era5-single-levels",
          variable=["2t", "2d", "msl", "sstk"],
          product_type="reanalysis",
          area=[50, -10, 40, 10],  # N,W,S,E
          grid=[2, 2],
          date="2012-05-10",
          time=[0, 12],
          split_on={"variable": 2, "time": 1},
      )

This will send 4 requests to the CDS:

    - variable=["2t", "2d"],  time=0
    - variable=["2t", "2d"],  time=12
    - variable=["msl", "sstk"], time=0
    - variable=["msl", "sstk"], time=12
