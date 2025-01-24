#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging
import os
import sys

import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import write_to_file

LOG = logging.getLogger(__name__)


def test_multi_graph_1():
    a11 = from_source("dummy-source", kind="grib", date=20000101)
    a12 = from_source("dummy-source", kind="grib", date=20000102)
    b11 = from_source("dummy-source", kind="grib", date=20000103)
    b12 = from_source("dummy-source", kind="grib", date=20000104)

    a21 = from_source("dummy-source", kind="grib", date=20000105)
    a22 = from_source("dummy-source", kind="grib", date=20000106)
    b21 = from_source("dummy-source", kind="grib", date=20000107)
    b22 = from_source("dummy-source", kind="grib", date=20000108)

    m1 = from_source(
        "multi",
        from_source("multi", a11, a12),
        from_source("multi", b11, b12),
    )

    m2 = from_source(
        "multi",
        from_source("multi", a21, a22),
        from_source("multi", b21, b22),
    )

    ds = from_source("multi", m1, m2)
    # ds.graph()

    assert len(ds) == 8
    ds.to_xarray()


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_multi_graph_2(write_method):
    with temp_directory() as tmpdir:
        os.mkdir(os.path.join(tmpdir, "a1"))
        a11 = from_source("dummy-source", kind="grib", date=20000101)
        write_to_file(write_method, os.path.join(tmpdir, "a1", "a11.grib"), a11)
        a12 = from_source("dummy-source", kind="grib", date=20000102)
        write_to_file(write_method, os.path.join(tmpdir, "a1", "a12.grib"), a12)

        os.mkdir(os.path.join(tmpdir, "b1"))
        b11 = from_source("dummy-source", kind="grib", date=20000103)
        write_to_file(write_method, os.path.join(tmpdir, "b1", "b11.grib"), b11)
        b12 = from_source("dummy-source", kind="grib", date=20000104)
        write_to_file(write_method, os.path.join(tmpdir, "b1", "b12.grib"), b12)

        os.mkdir(os.path.join(tmpdir, "a2"))
        a21 = from_source("dummy-source", kind="grib", date=20000105)
        write_to_file(write_method, os.path.join(tmpdir, "a2", "a21.grib"), a21)
        a22 = from_source("dummy-source", kind="grib", date=20000106)
        write_to_file(write_method, os.path.join(tmpdir, "a2", "a22.grib"), a22)

        os.mkdir(os.path.join(tmpdir, "b2"))
        b21 = from_source("dummy-source", kind="grib", date=20000107)
        write_to_file(write_method, os.path.join(tmpdir, "b2", "b21.grib"), b21)
        b22 = from_source("dummy-source", kind="grib", date=20000108)
        write_to_file(write_method, os.path.join(tmpdir, "b2", "b22.grib"), b22)

        def filter(path_or_url):
            return path_or_url.endswith("2.grib")

        ds = from_source("file", tmpdir, filter=filter)
        # ds.graph()

        assert len(ds) == 4


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.skipif(sys.platform == "win32", reason="Cannot unlink dir on Windows")
def test_multi_directory_1(write_method):
    with temp_directory() as directory:
        for date in (20000101, 20000102):
            ds = from_source("dummy-source", kind="grib", date=date)
            write_to_file(write_method, os.path.join(directory, f"{date}.grib"), ds)

        ds = from_source("file", directory)
        print(ds)
        assert len(ds) == 2
        ds.graph()

        with temp_file() as filename:
            write_to_file(write_method, filename, ds)
            ds = from_source("file", filename)
            assert len(ds) == 2


def test_multi_grib():
    ds = from_source(
        "multi",
        from_source("dummy-source", kind="grib", date=20000101),
        from_source("dummy-source", kind="grib", date=20000102),
    )
    assert len(ds) == 2
    ds.to_xarray()
    # ds.statistics()


def test_multi_grib_mixed():
    ds = from_source(
        "multi",
        from_source("dummy-source", kind="grib", date=20000101),
        from_source("dummy-source", kind="grib", date=20000102),
        from_source("dummy-source", kind="unknown", hello="world"),
    )
    assert len(ds) == 2


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
