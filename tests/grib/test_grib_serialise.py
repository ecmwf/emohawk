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
import pickle
import sys

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.readers.grib.metadata import StandAloneGribMetadata
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import write_to_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_NUMPY  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


def _pickle(data, representation):
    if representation == "file":
        with temp_file() as tmp:
            with open(tmp, "wb") as f:
                pickle.dump(data, f)

            with open(tmp, "rb") as f:
                data_res = pickle.load(f)
    elif representation == "memory":
        pickled_data = pickle.dumps(data)
        data_res = pickle.loads(pickled_data)
    else:
        raise ValueError(f"Invalid representation: {representation}")
    return data_res


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("representation", ["file", "memory"])
def test_grib_serialise_metadata(fl_type, representation):
    ds, _ = load_grib_data("test.grib", fl_type)
    md = ds[0].metadata().override()

    md2 = _pickle(md, representation)

    keys = ["param", "date", "time", "step", "level", "gridType", "type"]
    for k in keys:
        assert md[k] == md2[k]


@pytest.mark.parametrize("representation", ["file", "memory"])
def test_grib_serialise_standalone_metadata(representation):
    ds = from_source("file", earthkit_examples_file("test.grib"))

    md_ref = {
        "param": "2t",
        "date": 20200513,
        "time": 1200,
        "step": 0,
        "level": 0,
        "gridType": "regular_ll",
        "type": "an",
    }

    md = StandAloneGribMetadata(ds[0].handle)
    for k, v in md_ref.items():
        assert md[k] == v

    md2 = _pickle(md, representation)
    for k, v in md_ref.items():
        assert md2[k] == v


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("representation", ["file", "memory"])
def test_grib_serialise_array_field_memory(fl_type, representation):
    ds0, _ = load_grib_data("test.grib", fl_type)
    ds = ds0.to_fieldlist()

    for idx in range(len(ds)):
        f2 = _pickle(ds[idx], representation)

        assert np.allclose(ds[idx].values, f2.values), f"index={idx}"
        assert np.allclose(ds[idx].to_numpy(), f2.to_numpy()), f"index={idx}"

        keys = ["param", "date", "time", "step", "level", "gridType", "type"]
        for k in keys:
            assert ds[idx].metadata(k) == f2.metadata(k), f"index={idx}"


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("representation", ["file", "memory"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_serialise_array_fieldlist(fl_type, representation, write_method):
    ds0, _ = load_grib_data("test.grib", fl_type)
    ds = ds0.to_fieldlist()

    ds2 = _pickle(ds, representation)

    assert len(ds) == len(ds2)
    assert np.allclose(ds.values, ds2.values)

    keys = ["param", "date", "time", "step", "level", "gridType", "type"]
    for k in keys:
        ds2.metadata(k) == ds.metadata(k)

    r = ds2.sel(param="2t")
    assert len(r) == 1

    ds2[0]._array_ += 1
    v1 = ds[0]._array

    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds2)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        assert len(ds2) == len(r_tmp)
        v_tmp = r_tmp[0].to_numpy()
        assert np.allclose(v1 + 1, v_tmp)


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_serialise_file_fieldlist_core(fl_type):
    ds, _ = load_grib_data("test.grib", fl_type)

    pickled_f = pickle.dumps(ds)
    ds2 = pickle.loads(pickled_f)

    assert len(ds) == len(ds2)
    assert np.allclose(ds.values, ds2.values)

    keys = ["param", "date", "time", "step", "level", "gridType", "type"]
    for k in keys:
        ds2.metadata(k) == ds.metadata(k)

    r = ds2.sel(param="2t")
    assert len(r) == 1


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_serialise_file_fieldlist_sel(fl_type):
    ds0, _ = load_grib_data("test6.grib", fl_type)
    ds = ds0.sel(param="t")
    assert len(ds) == 2

    pickled_f = pickle.dumps(ds)
    ds2 = pickle.loads(pickled_f)

    assert len(ds2) == 2
    assert np.allclose(ds.values, ds2.values)

    keys = ["param", "date", "time", "step", "level", "gridType", "type"]
    for k in keys:
        ds2.metadata(k) == ds.metadata(k)

    r = ds2.sel(level=850)
    assert len(r) == 1


@pytest.mark.parametrize("fl_type", ["file"])
def test_grib_serialise_file_fieldlist_concat(fl_type):
    ds00, _ = load_grib_data("test.grib", fl_type)
    ds01, _ = load_grib_data("test6.grib", fl_type)
    ds = ds00 + ds01
    assert len(ds) == 8

    pickled_f = pickle.dumps(ds)
    ds2 = pickle.loads(pickled_f)

    assert len(ds2) == 8
    assert np.allclose(ds[:2].values, ds2[:2].values)
    assert np.allclose(ds[2:].values, ds2[2:].values)

    keys = ["param", "date", "time", "step", "level", "gridType", "type"]
    for k in keys:
        ds2.metadata(k) == ds.metadata(k)


def test_grib_serialise_stream_1():
    with open(earthkit_examples_file("test.grib"), "rb") as f:
        ds = from_source("stream", f)
        with pytest.raises(NotImplementedError):
            pickle.dumps(ds)


def test_grib_serialise_stream_2():
    with open(earthkit_examples_file("test.grib"), "rb") as f:
        ds = from_source("stream", f, read_all=True)
        pickled_f = pickle.dumps(ds)

    ds2 = pickle.loads(pickled_f)

    assert len(ds2) == 2
    assert ds.metadata("shortName") == ["2t", "msl"]


def test_grib_serialise_file_parts():
    parts = (240, 150)

    ds = from_source("file", earthkit_examples_file("test6.grib"), parts=parts)
    assert len(ds) == 1

    pickled_f = pickle.dumps(ds)
    ds2 = pickle.loads(pickled_f)

    assert len(ds2) == 1
    assert ds2[0].metadata(["param", "level"]) == ["u", 1000]
