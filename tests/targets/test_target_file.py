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

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.core.temporary import temp_file
from earthkit.data.encoders.grib import GribEncoder
from earthkit.data.targets import to_target
from earthkit.data.targets.file import FileTarget
from earthkit.data.testing import earthkit_examples_file


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"encoder": "grib"},
        {"encoder": GribEncoder()},
    ],
)
@pytest.mark.parametrize("direct_call", [True, False])
def test_target_file_grib_core(kwargs, direct_call):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_file() as path:
        if direct_call:
            to_target("file", path, data=ds, **kwargs)
        else:
            ds.to_target("file", path, **kwargs)

        ds1 = from_source("file", path)
        assert len(ds) == len(ds1)
        assert ds1.metadata("shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)


def test_target_file_grib_append():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_file() as path:
        ds.to_target("file", path)
        ds.to_target("file", path, append=True)

        ds1 = from_source("file", path)
        assert len(ds1) == len(ds) * 2
        assert ds1.metadata("shortName") == ["2t", "msl"] * 2
        assert np.allclose(ds1.values[:2, :4], vals_ref)
        assert np.allclose(ds1.values[2:, :4], vals_ref)


def test_target_file_grib_non_append():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    with temp_file() as path:
        ds.to_target("file", path)
        ds.to_target("file", path, append=False)

        ds1 = from_source("file", path)
        assert len(ds1) == 2


def test_target_file_grib_encoder_from_suffix():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_directory() as t_dir:
        path = os.path.join(t_dir, "_r.grib")
        ds.to_target("file", path)

        ds1 = from_source("file", path)
        assert len(ds) == len(ds1)
        assert ds1.metadata("shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"metadata": {"shortName": "2d", "bitsPerValue": 12}},
        {"encoder": "grib", "metadata": {"shortName": "2d", "bitsPerValue": 12}},
        {"encoder": GribEncoder(), "metadata": {"shortName": "2d", "bitsPerValue": 12}},
        {"encoder": GribEncoder(metadata={"shortName": "2d", "bitsPerValue": 12})},
    ],
)
def test_target_file_grib_set_metadata(kwargs):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_file() as path:
        ds.to_target("file", path, **kwargs)

        ds1 = from_source("file", path)
        assert len(ds) == len(ds1)
        assert ds1.metadata("shortName") == ["2d", "2d"]
        assert ds1.metadata("bitsPerValue") == [12, 12]
        assert np.allclose(ds1.values[:, :4], vals_ref, rtol=1e-1)


@pytest.mark.parametrize("per_field", [True, False])
def test_target_file_grib_direct_api(per_field):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_file() as path:
        target = FileTarget(path)
        if per_field:
            for f in ds:
                target.write(f)
        else:
            target.write(ds)
        target.close()

        ds1 = from_source("file", path)
        assert len(ds) == len(ds1)
        assert ds1.metadata("shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)


def test_target_file_grib_save_compat():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_file() as path:
        ds.save(path)

        ds1 = from_source("file", path)
        assert len(ds) == len(ds1)
        assert ds1.metadata("shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)


def test_target_file_grib_write_compat():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_file() as path:
        with open(path, "wb") as f:
            ds.write(f)

        ds1 = from_source("file", path)
        assert len(ds) == len(ds1)
        assert ds1.metadata("shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)


def test_target_file_bufr():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"))
    with temp_file() as path:
        ds.to_target("file", path)
        ds1 = from_source("file", path)
        assert len(ds1) == 10
        assert ds1[0].subset_count() == 1
        assert ds1[0].is_compressed() is False
        assert ds1[0].is_uncompressed() is False
        assert ds1[0].metadata("dataCategory") == 2
        assert ds1.metadata("dataCategory") == [2] * 10


def test_target_file_odb():
    ds = from_source("file", earthkit_examples_file("test.odb"))
    with temp_file() as path:
        ds.to_target("file", path)
        ds1 = from_source("file", path)
        df = ds1.to_pandas()
        assert len(df) == 717


def test_target_file_grib_to_netcdf():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    # vals_ref = ds.values[:, :4]

    with temp_file() as path:
        ds.to_target("file", path, encoder="netcdf")

        ds1 = from_source("file", path)
        assert len(ds1) == len(ds)
        assert ds1.metadata("param") == ["2t", "msl"]
        # assert np.allclose(ds1.values[:, :4], vals_ref)


def test_writers_core():
    # from earthkit.data.targets.file import FileTarget
    # from earthkit.data.targets import Target

    # from earthkit.data.targets import find_target
    # from earthkit.data.writers import to_target
    # from earthkit.data.writers import write

    # assert Target
    # assert find_target
    # assert write

    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_file() as path:
        ds.to_target("file", path)

        # assert path.exists()

        ds1 = from_source("file", path)
        assert len(ds) == len(ds1)
        assert ds1.metadata("shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)

    # write("file", ds, file=temp_file())
    # write("file", ds, encoder="grib", file=temp_file())

    # target = FileTarget(temp_file())
    # target.write(ds)
    # target.write(ds, encoder="grib")

    # to_target("file", ds, file=temp_file())
    # ds.to_target("file", file=temp_file(), encoder="grib")

    # to_target("fdb", ds, conf="myconf")
    # ds.to_target("fdb", conf="myconf")
    # target = FdbTarget("myconf")
    # target.write(ds)
    # target.write(ds, format="grib")
    # target.write(ds, encoder="grib")
