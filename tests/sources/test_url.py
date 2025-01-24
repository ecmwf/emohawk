#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import sys

import pytest

from earthkit.data import config
from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_remote_test_data_file
from earthkit.data.testing import network_off
from earthkit.data.testing import write_to_file


@pytest.mark.skipif(  # TODO: fix
    sys.platform == "win32",
    reason="file:// not working on Windows yet",
)
def test_url_file_source():
    filename = os.path.abspath(earthkit_examples_file("test.nc"))
    s = from_source("url", f"file://{filename}")
    assert len(s) == 2


def test_url_source_1():
    from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test.grib",
    )


@pytest.mark.cache
def test_url_source_check_out_of_date():
    def load():
        from_source(
            "url",
            "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test.grib",
        )

    with temp_directory() as tmpdir:
        with config.temporary():
            config.set("user-cache-directory", tmpdir)
            load()

            config.set("check-out-of-date-urls", False)
            with network_off():
                load()


def test_url_source_2():
    from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/earthkit-data/test-data/temp.bufr",
    )


def test_url_source_3():
    from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test.nc",
    )


def test_url_source_tar():
    ds = from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/test_gribs.tar",
    )
    assert len(ds) == 6


def test_parts_url():
    ds = from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/earthkit-data/test-data/temp.bufr",
    )

    ds = from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/earthkit-data/test-data/temp.bufr",
        parts=((0, 4),),
    )

    assert os.path.getsize(ds.path) == 4

    with open(ds.path, "rb") as f:
        assert f.read() == b"BUFR"

    ds = from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/earthkit-data/test-data/temp.bufr",
        parts=((0, 10), (50, 10), (60, 10)),
    )

    print(ds.path)

    assert os.path.getsize(ds.path) == 30

    with open(ds.path, "rb") as f:
        assert f.read()[:4] == b"BUFR"


def test_parts_as_arg_url_1():
    ds = from_source(
        "url",
        [
            "https://get.ecmwf.int/repository/test-data/earthkit-data/test-data/temp.bufr",
            [(0, 4)],
        ],
    )

    assert os.path.getsize(ds.path) == 4

    with open(ds.path, "rb") as f:
        assert f.read() == b"BUFR"


def test_parts_as_arg_url_2():
    ds = from_source(
        "url",
        [
            "https://get.ecmwf.int/repository/test-data/earthkit-data/test-data/temp.bufr",
            None,
        ],
    )

    assert os.path.getsize(ds.path) > 4

    with open(ds.path, "rb") as f:
        assert f.read(4) == b"BUFR"


def test_multi_url_parts_as_arg_invalid_1():
    with pytest.raises(ValueError):
        from_source(
            "url",
            [
                "https://get.ecmwf.int/repository/test-data/earthkit-data/test-data/temp.bufr",
                [(0, 4)],
            ],
            parts=[(0, 5)],
        )


def test_multi_url_parts_invalid():
    parts1 = [(240, 150)]
    parts2 = [(0, 526)]
    with pytest.raises(ValueError):
        from_source(
            "url",
            [
                [earthkit_remote_test_data_file("examples/test6.grib"), parts1],
                [earthkit_remote_test_data_file("examples/test.grib"), parts2],
            ],
            parts=[(0, 240)],
        )


@pytest.mark.skipif(  # TODO: fix
    sys.platform == "win32",
    reason="file:// not working on Windows yet",
)
def test_url_part_file_source():
    filename = os.path.abspath(earthkit_examples_file("test.grib"))
    ds = from_source(
        "url",
        f"file://{filename}",
        parts=[
            (0, 4),
            (522, 4),
            (526, 4),
            (1048, 4),
        ],
    )

    assert os.path.getsize(ds.path) == 16

    with open(ds.path, "rb") as f:
        assert f.read() == b"GRIB7777GRIB7777"


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_url_netcdf_source_save(write_method):
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("examples/test.nc"),
    )

    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        assert os.path.exists(tmp)
        ds_saved = from_source("file", tmp)
        assert len(ds_saved) == 2


if __name__ == "__main__":
    import logging

    from earthkit.data.testing import main

    logging.basicConfig(level=logging.DEBUG)
    main(__file__)
