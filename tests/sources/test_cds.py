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

import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.testing import NO_CDS
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import preserve_cwd
from earthkit.data.testing import write_to_file

CDS_TIMEOUT = pytest.CDS_TIMEOUT


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.parametrize("prompt", [True, False])
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_grib_prompt(prompt):
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        prompt=prompt,
        time="12:00",
    )
    assert len(s) == 2
    assert s.metadata("param") == ["2t", "msl"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_grib_kwargs():
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
    )
    assert len(s) == 2
    assert s.metadata("param") == ["2t", "msl"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_grib_dict():
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        dict(
            variable=["2t", "msl"],
            product_type="reanalysis",
            area=[50, -50, 20, 50],
            date="2012-12-12",
            time="12:00",
        ),
    )
    assert len(s) == 2
    assert s.metadata("param") == ["2t", "msl"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_grib_invalid_args_kwargs():
    with pytest.raises(TypeError):
        from_source(
            "cds",
            "reanalysis-era5-single-levels",
            dict(
                variable=["2t", "msl"],
                product_type="reanalysis",
                area=[50, -50, 20, 50],
                date="2012-12-12",
            ),
            time="12:00",
        )


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_grib_split_on_var():
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
        split_on="variable",
    )
    assert len(s) == 2
    assert s.metadata("param") == ["2t", "msl"]
    assert not hasattr(s, "path")
    assert len(s._indexes) == 2


@pytest.mark.parametrize(
    "date,expected_date",
    [
        (
            "2012-12-12/to/2012-12-14",
            [20121212, 20121212, 20121213, 20121213, 20121214, 20121214],
        ),
        (
            ["2014-05-12", "2014-05-13", "2014-05-14"],
            [20140512, 20140512, 20140513, 20140513, 20140514, 20140514],
        ),
    ],
)
@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_grib_multi_var_date(date, expected_date):
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date=date,
        time="12:00",
    )
    assert len(s) == 6
    assert s.metadata("param") == ["2t", "msl"] * 3
    assert s.metadata("date") == expected_date


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_cds_grib_save(write_method):
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
    )
    with temp_directory() as tmpdir:
        # Check file save to assigned filename
        write_to_file(write_method, os.path.join(tmpdir, "test.grib"), s)
        assert os.path.isfile(os.path.join(tmpdir, "test.grib"))

    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
    )
    with temp_directory() as tmpdir:
        # Check file can be saved in current dir with detected filename:
        with preserve_cwd():
            os.chdir(tmpdir)
            s.save()
            assert os.path.isfile(os.path.basename(s.source_filename))


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
@pytest.mark.parametrize(
    "split_on,expected_file_num,expected_param,expected_time",
    (
        [None, 1, ["2t", "msl", "2t", "msl"], [0, 0, 1200, 1200]],
        [[], 1, ["2t", "msl", "2t", "msl"], [0, 0, 1200, 1200]],
        [{}, 1, ["2t", "msl", "2t", "msl"], [0, 0, 1200, 1200]],
        ["variable", 2, ["2t", "2t", "msl", "msl"], [0, 1200] * 2],
        [("variable",), 2, ["2t", "2t", "msl", "msl"], [0, 1200, 0, 1200]],
        [{"variable": 1}, 2, ["2t", "2t", "msl", "msl"], [0, 1200, 0, 1200]],
        [{"variable": 1, "time": 2}, 2, ["2t", "2t", "msl", "msl"], [0, 1200, 0, 1200]],
        [{"variable": 2, "time": 1}, 2, ["2t", "msl", "2t", "msl"], [0, 0, 1200, 1200]],
        [("variable", "time"), 4, ["2t", "2t", "msl", "msl"], [0, 1200, 0, 1200]],
        [{"variable": 1, "time": 1}, 4, ["2t", "2t", "msl", "msl"], [0, 1200, 0, 1200]],
    ),
)
def test_cds_split_on(split_on, expected_file_num, expected_param, expected_time):
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time=["00:00", "12:00"],
        split_on=split_on,
    )

    if expected_file_num == 1:
        assert hasattr(s, "path")
        assert not hasattr(s, "_indexes")
    else:
        assert not hasattr(s, "path")
        assert len(s._indexes) == expected_file_num

    assert len(s) == 4
    assert s.metadata("param") == expected_param
    assert s.metadata("time") == expected_time


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
@pytest.mark.parametrize(
    "split_on1,split_on2,expected_file_num,expected_param,expected_time",
    (
        [None, None, 2, ["2t", "2t", "msl", "msl"], [0, 1200, 0, 1200]],
        [None, "time", 3, ["2t", "2t", "msl", "msl"], [0, 1200, 0, 1200]],
        ["time", "time", 4, ["2t", "2t", "msl", "msl"], [0, 1200, 0, 1200]],
    ),
)
def test_cds_multiple_requests(split_on1, split_on2, expected_file_num, expected_param, expected_time):
    base_request = dict(
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time=["00:00", "12:00"],
    )
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        {**base_request, **{"variable": "2t", "split_on": split_on1}},
        {**base_request, **{"variable": "msl", "split_on": split_on2}},
    )
    assert len(s._indexes) == expected_file_num
    assert len(s) == 4
    assert s.metadata("param") == expected_param
    assert s.metadata("time") == expected_time


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_netcdf():
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
        format="netcdf",
    )
    assert len(s) == 2
    assert s.metadata("variable") == ["t2m", "msl"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_netcdf_save():
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
        format="netcdf",
    )

    with temp_directory() as tmpdir:
        # Check file can be saved in current dir with detected filename:
        with preserve_cwd():
            os.chdir(tmpdir)
            s.save()
            assert os.path.isfile(os.path.basename(s.source_filename))


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(60)
def test_cds_netcdf_selection_limited():
    s = from_source(
        "cds",
        "satellite-albedo",
        {
            "variable": "albb_bh",
            "satellite": "noaa_7",
            "sensor": "avhrr",
            "product_version": "v2",
            "horizontal_resolution": "4km",
            "year": "1983",
            "month": "01",
            "nominal_day": "10",
        },
    )
    assert len(s) == 9
    assert s.metadata("variable") == [
        "AL_BH_BB",
        "AL_BH_BB_ERR",
        "AL_BH_NI",
        "AL_BH_NI_ERR",
        "AL_BH_VI",
        "AL_BH_VI_ERR",
        "AGE",
        "NMOD",
        "QFLAG",
    ]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_observation_csv_file_to_pandas_xarray():
    collection_id = "insitu-observations-gruan-reference-network"
    request = {
        "format": "csv-lev.zip",
        "year": "2006",
        "month": "05",
        "variable": ["air_temperature", "altitude"],
        "day": ["21", "22"],
    }
    data_cds = from_source("cds", collection_id, **request)
    data_file = from_source("file", data_cds.path)
    assert "report_timestamp" in data_cds.to_pandas().columns

    # Assert consistent behaviour for local and CDS versions
    assert data_cds.to_pandas().equals(data_file.to_pandas())
    assert data_cds.to_xarray().equals(data_file.to_xarray())

    df = data_file.to_pandas()
    assert len(df) == 11318
    assert list(df.columns)[:2] == ["station_name", "report_timestamp"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_non_observation_csv_file_to_pandas_xarray():
    collection_id = "sis-energy-derived-projections"
    request = {
        "format": "zip",
        "variable": "wind_power_generation_onshore",
        "spatial_aggregation": "country_level",
        "energy_product_type": "capacity_factor_ratio",
        "temporal_aggregation": "daily",
        "experiment": "rcp_2_6",
        "rcm": "hirham5",
        "gcm": "ec_earth",
    }
    data_cds = from_source("cds", collection_id, **request)
    assert "Date" in data_cds.to_pandas().columns

    # Assert a consistent behviour for local and remote versions
    data_file = from_source("file", data_cds.path)
    assert data_cds.to_pandas().equals(data_file.to_pandas())
    assert data_cds.to_xarray().equals(data_file.to_xarray())


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_grib_to_pandas_xarray():
    collection_id = "reanalysis-era5-single-levels"
    request = dict(
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12/to/2012-12-15",
        time="12:00",
    )
    data_cds = from_source("cds", collection_id, **request)

    # Assert a consistent behviour for local and remote versions
    data_file = from_source("file", data_cds.path)
    assert data_cds.to_pandas().equals(data_file.to_pandas())
    assert data_cds.to_xarray().equals(data_file.to_xarray())

    df = data_file.to_pandas()
    assert len(df) == 388168
    assert list(df.columns)[:3] == ["lat", "lon", "value"]

    ds = data_file.to_xarray()
    assert len(ds) == 2
    assert len(ds.data_vars) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.timeout(CDS_TIMEOUT)
def test_cds_netcdf_to_pandas_xarray():
    collection_id = "satellite-methane"
    request = {
        "format": "zip",
        "processing_level": "level_2",
        "variable": "xch4",
        "sensor_and_algorithm": "merged_emma",
        "version": "4.4",
        "year": "2021",
        "month": "01",
        "day": "01",
    }

    data_cds = from_source("cds", collection_id, **request)
    assert "xch4" in data_cds.to_xarray().data_vars

    # Assert a consistent behviour for local and remote versions
    data_file = from_source("file", data_cds.path)
    assert data_cds.to_xarray().equals(data_file.to_xarray())

    ds = data_file.to_xarray()
    assert len(ds) == 18
    assert len(ds.data_vars) == 18

    # TODO: implement to_dataframe
    # assert data_cds.to_pandas().equals(data_file.to_pandas())


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
