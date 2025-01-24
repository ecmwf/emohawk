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

import numpy as np
import pytest

from earthkit.data import FieldList
from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.sources.array_list import ArrayField
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import write_to_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_clone_metadata(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    def _func1(field, key, original_metadata):
        return original_metadata[key] + 100

    def _func2(field, key, original_metadata):
        return field.mars_area

    def _func3(field, key, original_metadata):
        return original_metadata.get("param") + "_" + str(original_metadata.get("levelist"))

    def _func4(field, key, original_metadata):
        return original_metadata[key] + 200

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].clone(
        param="q",
        levelist=_func1,
        mars_area=_func2,
        name=_func3,
    )

    assert f.metadata("param") == "q"
    assert f.metadata("shortName") == "t"
    assert f.metadata("level") == 500
    assert f.metadata("levelist") == 600
    assert f.metadata("date", "param") == (20070101, "q")
    assert f.metadata("param", "date") == ("q", 20070101)
    assert np.allclose(np.array(f.metadata("mars_area")), np.array([90.0, 0.0, -90.0, 359.0]))
    assert f.metadata("name") == "t_500"

    # TODO: apply wrapped metadata to namespaces
    assert f.metadata(namespace="mars") == {
        "class": "ea",
        "date": 20070101,
        "domain": "g",
        "expver": "0001",
        "levelist": 500,
        "levtype": "pl",
        "param": "t",
        "step": 0,
        "stream": "oper",
        "time": 1200,
        "type": "an",
    }

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        f = ds_ori[0].clone(
            param="q",
            levelist=_func1,
        )

        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.metadata("param") == "q"
        assert f_saved.metadata("shortName") == "q"
        assert f_saved.metadata("level") == 600
        assert f_saved.metadata("levelist") == 600

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].clone(
        param="q",
        levelist=_func1,
        mars_area=_func2,
        name=_func3,
    )

    f = f.clone(param="pt", levelist=_func4)

    assert f.metadata("param") == "pt"
    assert f.metadata("shortName") == "t"
    assert f.metadata("level") == 500

    # TODO: this should be 800
    assert f.metadata("levelist") == 700
    assert f.metadata("date", "param") == (20070101, "pt")
    assert f.metadata("param", "date") == ("pt", 20070101)
    assert np.allclose(np.array(f.metadata("mars_area")), np.array([90.0, 0.0, -90.0, 359.0]))
    assert f.metadata("name") == "t_500"

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        f = ds_ori[i].clone(
            param="q",
            levelist=_func1,
        )
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.metadata("param") == ["q", "q"]
    assert ds.metadata("shortName") == ["t", "z"]
    assert ds.metadata("level") == [500, 500]
    assert ds.metadata("levelist") == [600, 600]

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.metadata("param") == ["q", "q"]
        assert ds_saved.metadata("shortName") == ["q", "q"]
        assert ds_saved.metadata("level") == [600, 600]
        assert ds_saved.metadata("levelist") == [600, 600]

    # TODO: implement the following
    # serialise
    # pickled_f = pickle.dumps(ds)
    # ds_1 = pickle.loads(pickled_f)

    # assert ds_1.metadata("param") == ["q", "q"]
    # assert ds_1.metadata("shortName") == ["q", "q"]
    # assert ds_1.metadata("level") == [600, 600]
    # assert ds_1.metadata("levelist") == [600, 600]


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_clone_values(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].clone(values=vals_ori + 1)

    assert f.metadata("param") == "t"
    assert f.metadata("shortName") == "t"
    assert f.metadata("level") == 500
    assert f.metadata("levelist") == 500
    assert f.metadata("date", "param") == (20070101, "t")
    assert f.metadata("param", "date") == ("t", 20070101)
    assert np.allclose(f.values, vals_ori + 1)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.metadata("param") == "t"
        assert f_saved.metadata("shortName") == "t"
        assert f_saved.metadata("level") == 500
        assert f_saved.metadata("levelist") == 500
        assert np.allclose(f_saved.values, vals_ori + 1)

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].clone(values=vals_ori + 1)
    f = f.clone(values=vals_ori + 2)

    assert f.metadata("param") == "t"
    assert f.metadata("shortName") == "t"
    assert f.metadata("level") == 500
    assert f.metadata("levelist") == 500
    assert f.metadata("date", "param") == (20070101, "t")
    assert f.metadata("param", "date") == ("t", 20070101)
    assert np.allclose(f.values, vals_ori + 2)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        f = ds_ori[i].clone(values=vals_ori + i + 1)
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.metadata("param") == ["t", "z"]
    assert ds.metadata("shortName") == ["t", "z"]
    assert ds.metadata("level") == [500, 500]
    assert ds.metadata("levelist") == [500, 500]
    assert np.allclose(ds[0].values, vals_ori + 1)
    assert np.allclose(ds[1].values, vals_ori + 2)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.metadata("param") == ["t", "z"]
        assert ds_saved.metadata("shortName") == ["t", "z"]
        assert ds_saved.metadata("level") == [500, 500]
        assert ds_saved.metadata("levelist") == [500, 500]
        assert np.allclose(ds_saved[0].values, vals_ori + 1)
        assert np.allclose(ds_saved[1].values, vals_ori + 2)

    # TODO: implement the following
    # serialise
    # pickled_f = pickle.dumps(ds)
    # ds_1 = pickle.loads(pickled_f)

    # assert ds_1.metadata("param") == ["q", "q"]
    # assert ds_1.metadata("shortName") == ["q", "q"]
    # assert ds_1.metadata("level") == [600, 600]
    # assert ds_1.metadata("levelist") == [600, 600]


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_clone_combined(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    def _func1(field, key, original_metadata):
        return original_metadata[key] + 100

    def _func2(field, key, original_metadata):
        return original_metadata[key] + 200

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].clone(
        values=vals_ori + 1,
        param="q",
        levelist=_func1,
    )

    assert f.metadata("param") == "q"
    assert f.metadata("shortName") == "t"
    assert f.metadata("level") == 500
    assert f.metadata("levelist") == 600
    assert f.metadata("date", "param") == (20070101, "q")
    assert f.metadata("param", "date") == ("q", 20070101)
    assert np.allclose(f.values, vals_ori + 1)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.metadata("param") == "q"
        assert f_saved.metadata("shortName") == "q"
        assert f_saved.metadata("level") == 600
        assert f_saved.metadata("levelist") == 600
        assert np.allclose(f_saved.values, vals_ori + 1)

    # ---------------------
    # field - repeated use
    # ---------------------

    f = ds_ori[0].clone(
        values=vals_ori + 1,
        param="q",
        levelist=_func1,
    )
    f = f.clone(values=vals_ori + 2, param="pt", levelist=_func2)

    assert f.metadata("param") == "pt"
    assert f.metadata("shortName") == "t"
    assert f.metadata("level") == 500

    # this should be 800
    assert f.metadata("levelist") == 700
    assert f.metadata("date", "param") == (20070101, "pt")
    assert f.metadata("param", "date") == ("pt", 20070101)
    assert np.allclose(f.values, vals_ori + 2)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        f = ds_ori[i].clone(
            values=vals_ori + i + 1,
            param="q",
            levelist=_func1,
        )
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.metadata("param") == ["q", "q"]
    assert ds.metadata("shortName") == ["t", "z"]
    assert ds.metadata("level") == [500, 500]
    assert ds.metadata("levelist") == [600, 600]
    assert np.allclose(ds[0].values, vals_ori + 1)
    assert np.allclose(ds[1].values, vals_ori + 2)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.metadata("param") == ["q", "q"]
        assert ds_saved.metadata("shortName") == ["q", "q"]
        assert ds_saved.metadata("level") == [600, 600]
        assert ds_saved.metadata("levelist") == [600, 600]
        assert np.allclose(ds_saved[0].values, vals_ori + 1)
        assert np.allclose(ds_saved[1].values, vals_ori + 2)

    # TODO: implement the following
    # serialise
    # pickled_f = pickle.dumps(ds)
    # ds_1 = pickle.loads(pickled_f)

    # assert ds_1.metadata("param") == ["q", "q"]
    # assert ds_1.metadata("shortName") == ["q", "q"]
    # assert ds_1.metadata("level") == [600, 600]
    # assert ds_1.metadata("levelist") == [600, 600]


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_clone_default(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    # ---------------
    # field
    # ---------------

    f = ds_ori[0].clone()

    assert f.metadata("param") == "t"
    assert f.metadata("shortName") == "t"
    assert f.metadata("level") == 500
    assert f.metadata("levelist") == 500
    assert f.metadata("date", "param") == (20070101, "t")
    assert f.metadata("param", "date") == ("t", 20070101)
    assert np.allclose(f.values, vals_ori)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.metadata("param") == "t"
        assert f_saved.metadata("shortName") == "t"
        assert f_saved.metadata("level") == 500
        assert f_saved.metadata("levelist") == 500
        assert np.allclose(f_saved.values, vals_ori)


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_clone_with_metadata_object(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    md = ds_ori[0].metadata().override(shortName="q", level=600)

    f = ds_ori[0].clone(metadata=md)

    assert f.metadata("param") == "q"
    assert f.metadata("shortName") == "q"
    assert f.metadata("level") == 600
    assert f.metadata("levelist") == 600
    assert f.metadata("date", "param") == (20070101, "q")
    assert f.metadata("param", "date") == ("q", 20070101)
    assert np.allclose(f.values, vals_ori)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.metadata("param") == "q"
        assert f_saved.metadata("shortName") == "q"
        assert f_saved.metadata("level") == 600
        assert f_saved.metadata("levelist") == 600
        assert np.allclose(f_saved.values, vals_ori)

    with pytest.raises(ValueError):
        ds_ori[0].clone(metadata=md, param="q")


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_grib_copy_to_field(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    vals_ori = ds_ori[0].values

    # ---------------
    # field
    # ---------------

    md = (
        ds_ori[0]
        .metadata()
        .override(
            shortName="q",
            level=600,
        )
    )

    f = ds_ori[0].copy(
        values=vals_ori + 1,
        metadata=md,
    )

    assert isinstance(f, ArrayField)
    assert f.metadata("param") == "q"
    assert f.metadata("shortName") == "q"
    assert f.metadata("level") == 600
    assert f.metadata("levelist") == 600
    assert f.metadata("date", "param") == (20070101, "q")
    assert f.metadata("param", "date") == ("q", 20070101)
    assert np.allclose(f.values, vals_ori + 1)
    assert np.allclose(ds_ori[0].values, vals_ori)

    # write back to grib
    # we can only have ecCodes keys
    with temp_file() as tmp:
        write_to_file(write_method, tmp, f)
        f_saved = from_source("file", tmp)[0]
        assert f_saved.metadata("param") == "q"
        assert f_saved.metadata("shortName") == "q"
        assert f_saved.metadata("level") == 600
        assert f_saved.metadata("levelist") == 600
        assert np.allclose(f_saved.values, vals_ori + 1)

    # ---------------
    # fieldlist
    # ---------------

    fields = []
    for i in range(2):
        md = (
            ds_ori[i]
            .metadata()
            .override(
                shortName="q",
                level=600,
            )
        )
        f = ds_ori[i].copy(
            values=vals_ori + i + 1,
            metadata=md,
        )
        assert isinstance(f, ArrayField)
        fields.append(f)

    ds = FieldList.from_fields(fields)

    assert ds.metadata("param") == ["q", "q"]
    assert ds.metadata("shortName") == ["q", "q"]
    assert ds.metadata("level") == [600, 600]
    assert ds.metadata("levelist") == [600, 600]
    assert np.allclose(ds[0].values, vals_ori + 1)
    assert np.allclose(ds[1].values, vals_ori + 2)

    # write back to grib
    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        ds_saved = from_source("file", tmp)
        assert ds_saved.metadata("param") == ["q", "q"]
        assert ds_saved.metadata("shortName") == ["q", "q"]
        assert ds_saved.metadata("level") == [600, 600]
        assert ds_saved.metadata("levelist") == [600, 600]
        assert np.allclose(ds_saved[0].values, vals_ori + 1)
        assert np.allclose(ds_saved[1].values, vals_ori + 2)
