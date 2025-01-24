#!/usr/bin/env python3

# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import os
import sys
import tempfile

import numpy as np
import pytest

import earthkit.data
from earthkit.data import from_source
from earthkit.data import to_target
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import write_to_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_ARRAYS  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402

EPSILON = 1e-4


def new_grib_output_compat(*args, **kwargs):
    from earthkit.data.targets.file import FileTarget

    return FileTarget(*args, encoder="grib", **kwargs)


def new_grib_coder_compat(*args, **kwargs):
    from earthkit.data.encoders.grib import GribEncoder

    return GribEncoder(*args, **kwargs)


@pytest.mark.parametrize("fl_type", FL_ARRAYS)
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_save_when_loaded_from_file(fl_type, write_method):
    fs, _ = load_grib_data("test6.grib", fl_type)
    assert len(fs) == 6
    with temp_file() as tmp:
        write_to_file(write_method, tmp, fs)
        fs_saved = from_source("file", tmp)
        assert len(fs) == len(fs_saved)


@pytest.mark.parametrize(
    "_kwargs,expected_value",
    [({}, 16), ({"bits_per_value": 12}, 12), ({"bits_per_value": None}, 16)],
)
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_save_bits_per_value(_kwargs, expected_value, write_method):
    ds = from_source("file", earthkit_examples_file("test.grib"))

    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds, **_kwargs)
        ds1 = from_source("file", tmp)
        assert ds1.metadata("bitsPerValue") == [expected_value] * len(ds)


# TODO: if we use missing_value = np.finfo(np.float32).max the test fails
@pytest.mark.parametrize("mode", ["ori", "compat", "target"])
@pytest.mark.parametrize("missing_value", [100000.0, np.finfo(np.float32).max - 1])
def test_grib_output_missing_value_1(mode, missing_value):
    fld = from_source("file", earthkit_examples_file("test.grib"))[0]

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        values = fld.values
        values[0] = np.nan
        assert not np.isnan(values[1])

        if mode == "ori":
            f = earthkit.data.new_grib_output(path)
            f.write(values, check_nans=True, missing_value=missing_value, template=fld)
            f.close()
        elif mode == "compat":
            f = new_grib_output_compat(path)
            f.write(values=values, check_nans=True, missing_value=missing_value, template=fld)
            f.close()
        elif mode == "target":
            to_target(
                "file",
                path,
                values=values,
                template=fld,
                check_nans=True,
                missing_value=missing_value,
            )
        ds = earthkit.data.from_source("file", path)
        assert ds[0].metadata("bitmapPresent") == 1
        assert np.isnan(ds[0].values[0])
        assert not np.isnan(values[1])


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["ori", "compat", "target"])
def test_grib_output_latlon(mode):
    data = np.random.random((181, 360))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        if mode == "ori":
            f = earthkit.data.new_grib_output(path, date=20010101)
            f.write(data, param="2t")
            f.close()
        elif mode == "compat":
            f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
            f.write(values=data, param="2t")
            f.close()
        elif mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
                values=data,
            )

        ds = earthkit.data.from_source("file", path)
        print(ds[0])

        assert ds[0].metadata("date") == 20010101
        assert ds[0].metadata("param") == "2t"
        assert ds[0].metadata("levtype") == "sfc"
        assert ds[0].metadata("edition") == 2
        assert ds[0].metadata("generatingProcessIdentifier") == 255

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["ori", "compat", "target"])
def test_grib_output_o96_sfc(mode):
    data = np.random.random((40320,))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        if mode == "ori":
            f = earthkit.data.new_grib_output(path, date=20010101)
            f.write(data, param="2t")
            f.close()
        elif mode == "compat":
            f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
            f.write(values=data, param="2t")
            f.close()
        elif mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
                values=data,
            )

        ds = earthkit.data.from_source("file", path)

        ref = {
            "date": 20010101,
            "param": "2t",
            "levtype": "sfc",
            "edition": 2,
            "generatingProcessIdentifier": 255,
            "gridType": "reduced_gg",
            "N": 96,
            "isOctahedral": 1,
        }

        for k, v in ref.items():
            assert ds[0].metadata(k) == v, f"{k}: {ds[0].metadata(k)}!={v}"

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["ori", "compat", "target"])
def test_grib_output_o160_sfc(mode):
    data = np.random.random((108160,))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        if mode == "ori":
            f = earthkit.data.new_grib_output(path, date=20010101)
            f.write(data, param="2t")
            f.close()
        elif mode == "compat":
            f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
            f.write(values=data, param="2t")
            f.close()
        elif mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
                values=data,
            )
        ds = earthkit.data.from_source("file", path)

        ref = {
            "date": 20010101,
            "param": "2t",
            "levtype": "sfc",
            "edition": 2,
            "generatingProcessIdentifier": 255,
            "gridType": "reduced_gg",
            "N": 160,
            "isOctahedral": 1,
        }

        for k, v in ref.items():
            assert ds[0].metadata(k) == v, f"{k}: {ds[0].metadata(k)}!={v}"

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["ori", "compat", "target"])
def test_grib_output_n96_sfc(mode):
    data = np.random.random(50662)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        if mode == "ori":
            f = earthkit.data.new_grib_output(path, date=20010101)
            f.write(data, param="2t")
            f.close()
        elif mode == "compat":
            f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
            f.write(values=data, param="2t")
            f.close()
        else:
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="2t"),
                values=data,
            )
        ds = earthkit.data.from_source("file", path)

        ref = {
            "date": 20010101,
            "param": "2t",
            "levtype": "sfc",
            "edition": 2,
            "generatingProcessIdentifier": 255,
            "gridType": "reduced_gg",
            "N": 96,
            "isOctahedral": 0,
        }

        for k, v in ref.items():
            assert ds[0].metadata(k) == v, f"{k}: {ds[0].metadata(k)}!={v}"

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["ori", "compat", "target"])
def test_grib_output_mars_labeling(mode):
    data = np.random.random((40320,))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        if mode == "ori":
            f = earthkit.data.new_grib_output(path, date=20010101)
            f.write(data, type="fc", expver="test", step=24, param="msl")
            f.close()
        elif mode == "compat":
            f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
            f.write(values=data, type="fc", expver="test", step=24, param="msl")
            f.close()
        elif mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(
                    date=20010101,
                    generatingProcessIdentifier=255,
                    type="fc",
                    expver="test",
                    step=24,
                    param="msl",
                ),
                values=data,
            )

        ds = earthkit.data.from_source("file", path)

        assert ds[0].metadata("date") == 20010101
        assert ds[0].metadata("edition") == 2
        assert ds[0].metadata("step", astype=int) == 24
        assert ds[0].metadata("expver") == "test"
        assert ds[0].metadata("levtype") == "sfc"
        assert ds[0].metadata("param") == "msl"
        assert ds[0].metadata("type") == "fc"
        assert ds[0].metadata("generatingProcessIdentifier") == 255
        assert ds[0].metadata("gridType") == "reduced_gg"
        assert ds[0].metadata("N") == 96
        assert ds[0].metadata("isOctahedral") == 1

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["ori", "compat", "target"])
@pytest.mark.parametrize("levtype", [{}, {"levtype": "pl"}])
def test_grib_output_o96_pl(mode, levtype):
    data = np.random.random((40320,))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        if mode == "ori":
            f = earthkit.data.new_grib_output(path, date=20010101)
            _kwargs = dict(param="t", level=850)
            _kwargs.update(levtype)
            f.write(data, **_kwargs)
            f.close()
        elif mode == "compat":
            f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
            _kwargs = dict(param="t", level=850)
            _kwargs.update(levtype)
            f.write(values=data, **_kwargs)
            f.close()
        elif mode == "target":
            _kwargs = dict(date=20010101, generatingProcessIdentifier=255, param="t", level=850)
            _kwargs.update(levtype)
            to_target("file", path, metadata=_kwargs, values=data)

        ds = earthkit.data.from_source("file", path)

        assert ds[0].metadata("date") == 20010101
        assert ds[0].metadata("edition") == 2
        assert ds[0].metadata("level") == 850
        assert ds[0].metadata("levtype") == "pl"
        assert ds[0].metadata("param") == "t"
        assert ds[0].metadata("generatingProcessIdentifier") == 255
        assert ds[0].metadata("gridType") == "reduced_gg"
        assert ds[0].metadata("N") == 96
        assert ds[0].metadata("isOctahedral") == 1

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["ori", "compat", "target"])
@pytest.mark.parametrize("levtype", [{}, {"levtype": "pl"}])
def test_grib_output_tp(mode, levtype):
    data = np.random.random((181, 360))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = os.path.join(tmp, "a.grib")

        if mode == "ori":
            f = earthkit.data.new_grib_output(path, date=20010101)
            # TODO: make it work for edition=2
            f.write(data, param="tp", step=48, edition=1)
            f.close()
        elif mode == "compat":
            f = new_grib_output_compat(path, metadata=dict(date=20010101, generatingProcessIdentifier=255))
            # TODO: make it work for edition=2
            f.write(values=data, param="tp", step=48, edition=1)
            f.close()
        elif mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="tp", step=48, edition=1),
                values=data,
            )
        ds = earthkit.data.from_source("file", path)

        assert ds[0].metadata("date") == 20010101
        assert ds[0].metadata("param") == "tp"
        assert ds[0].metadata("levtype") == "sfc"
        assert ds[0].metadata("edition") == 1
        assert ds[0].metadata("step", astype=int) == 48
        assert ds[0].metadata("generatingProcessIdentifier") == 255
        assert ds[0].metadata("gridType") == "regular_ll"
        assert ds[0].metadata("Ni") == 360
        assert ds[0].metadata("Nj") == 181

        assert np.allclose(ds[0].to_numpy(), data, rtol=EPSILON, atol=EPSILON)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="ignore_cleanup_errors requires Python 3.10 or later",
)
@pytest.mark.parametrize("mode", ["ori", "compat", "target"])
@pytest.mark.parametrize("array", [True, False])
def test_grib_output_field_template(mode, array):
    data = np.random.random((7, 12))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        ds = from_source("file", earthkit_examples_file("test6.grib"))
        if array:
            ds = ds.to_fieldlist()

        assert ds[0].metadata("bitsPerValue") == 4

        path = os.path.join(tmp, "a.grib")

        if mode == "ori":
            f = earthkit.data.new_grib_output(path, template=ds[0], date=20010101)
            f.write(data, param="pt", bitsPerValue=16)
            f.close()
        elif mode == "compat":
            f = new_grib_output_compat(
                path, template=ds[0], metadata=dict(date=20010101, generatingProcessIdentifier=255)
            )
            f.write(values=data, param="pt", bitsPerValue=16)
            f.close()
        elif mode == "target":
            to_target(
                "file",
                path,
                metadata=dict(date=20010101, generatingProcessIdentifier=255, param="pt", bitsPerValue=16),
                values=data,
                template=ds[0],
            )

        ds = earthkit.data.from_source("file", path)

        assert ds[0].metadata("date") == 20010101
        assert ds[0].metadata("param") == "pt"
        assert ds[0].metadata("levtype") == "pl"
        assert ds[0].metadata("edition") == 1
        assert ds[0].metadata("generatingProcessIdentifier") == 255
        assert ds[0].metadata("bitsPerValue") == 16

        assert np.allclose(ds[0].to_numpy(), data, rtol=1e-2, atol=1e-2)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
