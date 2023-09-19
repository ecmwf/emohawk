.. _howtos


Howtos
============


How to save results from a retrieval into a file?
--------------------------------------------------------------

You need to use the :func:`save` method on the resulting object. For example, this is how to
save the results of a :ref:`MARS retrieval <data-sources-mars>` into a file:

.. code-block:: python

    import earthkit.data

    ds = earthkit.data.from_source(
        "mars",
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -10, 40, 10],  # N,W,S,E
        grid=[2, 2],
        date="2023-05-10",
    )

    ds.save("my_data.grib")
