#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import os
import tempfile

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.readers.netcdf.field import NetCDFField
from earthkit.data.testing import NO_CDS
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_file
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.testing import write_to_file


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


@pytest.mark.no_eccodes
def test_netcdf_reader():
    ds = from_source("file", earthkit_file("docs/examples/test.nc"))
    # assert str(ds).startswith("NetCDFReader"), r
    assert len(ds) == 2
    assert isinstance(ds[0], NetCDFField)
    assert isinstance(ds[1], NetCDFField)
    for f in from_source("file", earthkit_file("docs/examples/test.nc")):
        assert isinstance(f, NetCDFField)


@pytest.mark.parametrize("attribute", ["coordinates", "bounds", "grid_mapping"])
def test_dummy_netcdf_reader_2(attribute):
    s = from_source(
        "dummy-source",
        kind="netcdf",
        attributes={"a": {attribute: f"{attribute}_of_a"}},
        variables=["a", f"{attribute}_of_a"],
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims
    assert len(s) == 1
    # s.to_datetime_list()
    s.bounding_box()


def test_dummy_netcdf():
    s = from_source("dummy-source", kind="netcdf")
    ds = s.to_xarray()
    assert "lat" in ds.dims


def test_dummy_netcdf_2():
    s = from_source("dummy-source", kind="netcdf", dims=["lat", "lon", "time"], variables=["a", "b"])
    ds = s.to_xarray()
    assert "lat" in ds.dims


def test_dummy_netcdf_3():
    s = from_source(
        "dummy-source",
        kind="netcdf",
        dims={"lat": dict(size=3), "lon": dict(size=2), "time": dict(size=2)},
        variables=["a", "b"],
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims


def test_dummy_netcdf_4():
    s = from_source(
        "dummy-source",
        kind="netcdf",
        dims={"lat": dict(size=3), "lon": dict(size=2), "time": dict(size=2)},
        variables={
            "a": dict(dims=["lat", "lon"]),
            "b": dict(dims=["lat", "time"]),
        },
    )
    ds = s.to_xarray()
    assert "lat" in ds.dims


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_netcdf_multi_cds():
    s1 = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        product_type="reanalysis",
        param="2t",
        date="2021-03-01",
        grid=[20, 20],
        format="netcdf",
    )
    s1.to_xarray()
    s2 = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        product_type="reanalysis",
        param="2t",
        date="2021-03-02",
        grid=[20, 20],
        format="netcdf",
    )
    s2.to_xarray()

    source = from_source("multi", s1, s2)
    for s in source:
        print(s)

    # TODO: this is crashing with new CDS
    # source.to_xarray()


@pytest.mark.no_eccodes
def test_netcdf_multi_sources():
    path = earthkit_test_data_file("era5_2t_1.nc")
    s1 = from_source("file", path)
    s1.to_xarray()
    assert s1.path == path

    path = earthkit_test_data_file("era5_2t_2.nc")
    s2 = from_source("file", path)
    s2.to_xarray()
    assert s2.path == path

    s3 = from_source("multi", s1, s2)
    for s in s3:
        print(s)

    assert len(s3) == 2
    assert s3[0].datetime() == {
        "base_time": datetime.datetime(2021, 3, 1, 12, 0),
        "valid_time": datetime.datetime(2021, 3, 1, 12, 0),
    }
    assert s3[1].datetime() == {
        "base_time": datetime.datetime(2021, 3, 2, 12, 0),
        "valid_time": datetime.datetime(2021, 3, 2, 12, 0),
    }
    assert s3.datetime() == {
        "base_time": [
            datetime.datetime(2021, 3, 1, 12, 0),
            datetime.datetime(2021, 3, 2, 12, 0),
        ],
        "valid_time": [
            datetime.datetime(2021, 3, 1, 12, 0),
            datetime.datetime(2021, 3, 2, 12, 0),
        ],
    }
    s3.to_xarray()


@pytest.mark.no_eccodes
def test_netcdf_multi_files():
    ds = from_source(
        "file",
        [
            earthkit_test_data_file("era5_2t_1.nc"),
            earthkit_test_data_file("era5_2t_2.nc"),
        ],
    )

    assert len(ds) == 2
    assert ds[0].datetime() == {
        "base_time": datetime.datetime(2021, 3, 1, 12, 0),
        "valid_time": datetime.datetime(2021, 3, 1, 12, 0),
    }
    assert ds[1].datetime() == {
        "base_time": datetime.datetime(2021, 3, 2, 12, 0),
        "valid_time": datetime.datetime(2021, 3, 2, 12, 0),
    }
    assert ds.datetime() == {
        "base_time": [
            datetime.datetime(2021, 3, 1, 12, 0),
            datetime.datetime(2021, 3, 2, 12, 0),
        ],
        "valid_time": [
            datetime.datetime(2021, 3, 1, 12, 0),
            datetime.datetime(2021, 3, 2, 12, 0),
        ],
    }

    ds.to_xarray()


@pytest.mark.no_eccodes
def test_get_fields_missing_standard_name_attr_in_coord_array():
    """test _get_fields() can handle a missing 'standard_name' attr in coordinate data arrays"""

    # example dataset
    fs = from_source("file", earthkit_examples_file("test.nc"))
    ds = fs.to_xarray()

    # delete 'standard_name' attribute (if exists) in any coordinate data arrays
    for coord_name in ds.coords:
        try:
            del ds.coords[coord_name].attrs["standard_name"]
        except Exception as e:
            print(e)

    # save updates to disk and try read that file source
    with tempfile.TemporaryDirectory() as tmp_dir:
        fpath = os.path.join(tmp_dir, "tmp.nc")
        ds.to_netcdf(fpath)
        fs = from_source("file", earthkit_test_data_file(fpath))
        assert len(fs) == 2


# @pytest.mark.no_eccodes
# def test_netcdf_non_fieldlist_0():
#     ek_ch4_l2 = from_source(
#         "url",
#         earthkit_remote_test_data_file(
#             "test-data/20210101-C3S-L2_GHG-GHG_PRODUCTS-TANSO2-GOSAT2-SRFP-DAILY-v2.0.0.nc"
#         ),
#         # Data from this CDS request:
#         # "cds",
#         # "satellite-methane",
#         # {
#         #     "processing_level": "level_2",
#         #     "sensor_and_algorithm": "tanso2_fts2_srfp",
#         #     "year": "2021",
#         #     "month": "01",
#         #     "day": "01",
#         #     "version": "2.0.0",
#         # },
#     )
#     # TODO: add more conditions to this test when it is clear what methods it should have
#     ek_ch4_l2.to_xarray()


@pytest.mark.no_eccodes
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_netcdf_non_fieldlist(write_method):
    ds = from_source("file", earthkit_test_data_file("hovexp_vert_area.nc"))
    with pytest.raises(TypeError):
        len(ds)

    import xarray as xr

    ref = xr.open_dataset(earthkit_test_data_file("hovexp_vert_area.nc"))
    res = ds.to_xarray()

    assert ref.identical(res)
    assert ds.to_numpy().shape == (1, 6, 5)

    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        assert os.path.exists(tmp)
        ds_saved = from_source("file", tmp)
        assert ds_saved.to_xarray().identical(res)


@pytest.mark.no_eccodes
def test_netcdf_lazy_fieldlist_scan():
    ds = from_source("file", earthkit_examples_file("test.nc"))
    # assert ds._reader._fields is None
    assert ds._fields is None
    assert len(ds) == 2
    # assert len(ds._reader._fields) == 2
    assert len(ds._fields) == 2


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
