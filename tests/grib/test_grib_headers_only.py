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
import yaml

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.readers.grib.metadata import RestrictedGribMetadata
from earthkit.data.readers.grib.metadata import StandAloneGribMetadata
from earthkit.data.readers.grib.metadata import WrappedMetadata
from earthkit.data.readers.grib.output import new_grib_output
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_remote_test_data_file
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.utils import ensure_iterable


def to_tuple(x):
    return tuple(ensure_iterable(x))


def grid_list(files=None, skip=None):
    with open(earthkit_test_data_file(os.path.join("xr_engine", "xr_grid.yaml")), "r") as f:
        r = yaml.safe_load(f)

    files = [] if files is None else files
    skip = [] if skip is None else skip
    for item in r:
        if not files or item["file"] in files and item["file"] not in skip:
            yield item["file"]


def check_field_write(f, md_ref, shape_ref, values_ref, use_writer=False, **kwargs):
    with temp_file() as tmp:
        if use_writer:
            fp = new_grib_output(tmp, template=f, **kwargs)
            fp.write(f.values)
            fp.close()
        else:
            f.save(tmp, **kwargs)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        assert len(r_tmp) == 1
        f = r_tmp[0]
        md = {k: f.metadata(k) for k in md_ref}
        md_ref_tmp = dict(**md_ref)

        # for single point data, the original bitsPerValue is 12. In the cloned handle it becomes 0.
        # For some reason when we try to set it again in the clone it results in 0!
        if len(values_ref) == 1:
            md_ref_tmp["bitsPerValue"] = 0

        assert md == md_ref_tmp

        assert f.shape == shape_ref
        assert len(f.values) == len(values_ref)
        if md["gridType"] != "sh":
            assert np.allclose(f.values, values_ref, rtol=1e-1)


# @pytest.mark.skipif(True, reason="headers_only_clone has to be fixed")
def test_grib_metadata_override_headers_only_true_core():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    ref_size = ds[0].metadata("totalLength")

    md1 = ds[0].metadata().override(headers_only_clone=True)
    assert isinstance(md1, WrappedMetadata)
    assert md1._handle is not None
    assert md1._handle != ds[0]._handle
    assert md1["totalLength"] - ref_size < -10
    assert md1["bitsPerValue"] == 16
    assert md1["shortName"] == "2t"
    assert md1["typeOfLevel"] == "surface"

    md2 = md1._hide_internal_keys()
    assert isinstance(md2, RestrictedGribMetadata)
    assert md2._handle is not None
    assert md2._handle != ds[0]._handle
    assert md2._handle == md1._handle
    assert md2.extra == {"bitsPerValue": 16}
    assert md2["bitsPerValue"] == 16
    assert md2["shortName"] == "2t"
    assert md2["typeOfLevel"] == "surface"

    with pytest.raises(KeyError):
        md2["average"]

    md3 = md2.override(headers_only_clone=True, shortName="2d")
    assert isinstance(md3, RestrictedGribMetadata)
    assert md3._handle is not None
    assert md3._handle != ds[0]._handle
    assert md3._handle != md1._handle
    assert md3._handle != md2._handle
    assert md3["totalLength"] - ref_size < -10
    assert md3.extra == {"bitsPerValue": 16}
    assert md3["bitsPerValue"] == 16
    assert md3["shortName"] == "2d"
    assert md3["typeOfLevel"] == "surface"

    md4 = md3._hide_internal_keys()
    assert md4 is md3

    md5 = md3.override(headers_only_clone=True, bitsPerValue=8)
    assert isinstance(md5, RestrictedGribMetadata)
    assert md5._handle is not None
    assert md5._handle != ds[0]._handle
    assert md5._handle != md1._handle
    assert md5._handle != md3._handle
    assert md5["totalLength"] - ref_size < -10
    assert md5.extra == {"bitsPerValue": 8}
    assert md5["bitsPerValue"] == 8
    assert md5["shortName"] == "2d"
    assert md5["typeOfLevel"] == "surface"


def test_grib_metadata_override_headers_only_false_core():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    ref_size = ds[0].metadata("totalLength")

    md1 = ds[0].metadata().override(headers_only_clone=False)
    assert isinstance(md1, WrappedMetadata)
    assert isinstance(md1.metadata, StandAloneGribMetadata)
    assert md1._handle is not None
    assert md1._handle != ds[0]._handle
    assert np.isclose(md1["totalLength"], ref_size)

    md2 = md1._hide_internal_keys()
    assert isinstance(md2, RestrictedGribMetadata)
    assert isinstance(md2.metadata, StandAloneGribMetadata)
    assert md2._handle is not None
    assert md2._handle != ds[0]._handle
    assert md2._handle == md1._handle

    with pytest.raises(KeyError):
        md2["average"]


@pytest.mark.cache
@pytest.mark.parametrize(
    "file",
    # grid_list(files=["regular_ll_single_point.grib1"]),
    grid_list(),
)
def test_grib_metadata_headers_only_clone_true_grids(file):
    ds0 = from_source("url", earthkit_remote_test_data_file("test-data", "xr_engine", "grid", file))

    keys = ["bitsPerValue", "level", "shortName", "gridType", "packingType", "date"]
    md_ref = {k: ds0[0].metadata(k) for k in keys}
    shape_ref = ds0[0].shape
    vals_ref = ds0[0].values

    # array field
    ds = ds0.to_fieldlist()
    md = {k: ds[0].metadata(k) for k in keys}
    assert isinstance(ds[0].metadata(), RestrictedGribMetadata)
    assert md == md_ref
    assert ds[0].shape == shape_ref

    # create new field with modified metadata
    f = ds[0].copy(metadata=ds[0].metadata().override(date=19810102))
    assert isinstance(f.metadata(), RestrictedGribMetadata)
    md_ref_1 = dict(**md_ref)
    md_ref_1["date"] = 19810102
    md = {k: f.metadata(k) for k in keys}
    assert md == md_ref_1

    # save to disk, should use the original bitsPerValue

    # for single point data, the original bitsPerValue is 12. In the cloned handle it becomes 0.
    # For some reason when we try to set it again to 12 on the clone it results in 0!
    check_field_write(f, md_ref_1, shape_ref, vals_ref)

    # save to disk, with the given bitsPerValue
    md_ref_tmp = dict(**md_ref_1)
    md_ref_tmp["bitsPerValue"] = 24
    check_field_write(f, md_ref_tmp, shape_ref, vals_ref, bitsPerValue=24)

    # create new field with modified bitsPerValue
    f = f.copy(metadata=f.metadata().override(bitsPerValue=8))
    assert isinstance(f.metadata(), RestrictedGribMetadata)
    md_ref_1["bitsPerValue"] = 8
    md = {k: f.metadata(k) for k in keys}
    assert md == md_ref_1

    # save to disk, with the given bitsPerValue
    check_field_write(f, md_ref_1, shape_ref, vals_ref)

    # save to disk, with the given bitsPerValue
    check_field_write(f, md_ref_1, shape_ref, vals_ref, use_writer=True)


@pytest.mark.cache
@pytest.mark.parametrize(
    "file",
    # grid_list(files=["reduced_gg_N32.grib1"]),
    grid_list(),
)
def test_grib_metadata_headers_only_clone_false_grids(file):
    ds0 = from_source("url", earthkit_remote_test_data_file("test-data", "xr_engine", "grid", file))

    keys = ["bitsPerValue", "level", "shortName", "gridType", "packingType", "date"]
    md_ref = {k: ds0[0].metadata(k) for k in keys}
    shape_ref = ds0[0].shape
    vals_ref = ds0[0].values

    # array field
    ds = ds0.from_fields([ds0[0].copy(metadata=ds0[0].metadata().override(headers_only_clone=False))])
    md = {k: ds[0].metadata(k) for k in keys}
    assert isinstance(ds[0].metadata(), RestrictedGribMetadata)
    assert md == md_ref
    assert ds[0].shape == shape_ref

    # create new field with modified metadata
    f = ds[0].copy(metadata=ds[0].metadata().override(headers_only_clone=False, date=19810102))
    assert isinstance(f.metadata(), RestrictedGribMetadata)
    md_ref_1 = dict(**md_ref)
    md_ref_1["date"] = 19810102
    md = {k: f.metadata(k) for k in keys}
    assert md == md_ref_1

    # save to disk, should use the original bitsPerValue

    # for single point data, the original bitsPerValue is 12. In the cloned handle it becomes 0.
    # For some reason when we try to set it again to 12 on the clone it results in 0!
    check_field_write(f, md_ref_1, shape_ref, vals_ref)

    # save to disk, with the given bitsPerValue
    md_ref_tmp = dict(**md_ref_1)
    md_ref_tmp["bitsPerValue"] = 24
    check_field_write(f, md_ref_tmp, shape_ref, vals_ref, bitsPerValue=24)

    # create new field with modified bitsPerValue
    f = f.copy(metadata=f.metadata().override(bitsPerValue=8, headers_only_clone=False))
    assert isinstance(f.metadata(), RestrictedGribMetadata)
    md_ref_1["bitsPerValue"] = 8
    md = {k: f.metadata(k) for k in keys}
    assert md == md_ref_1

    # save to disk, with the given bitsPerValue
    check_field_write(f, md_ref_1, shape_ref, vals_ref)

    # save to disk, with the given bitsPerValue
    check_field_write(f, md_ref_1, shape_ref, vals_ref, use_writer=True)


def test_grib_headers_only_clone_standalone_metadata():
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

    md0 = ds[0].metadata().override()
    md1 = StandAloneGribMetadata(md0._handle)
    for k, v in md_ref.items():
        assert md1[k] == v

    # the handle does not contain bitsPerValue
    assert md1["bitsPerValue"] == 0

    md0 = ds[0].metadata().override(bitsPerValue=8)
    md1 = StandAloneGribMetadata(md0._handle)
    for k, v in md_ref.items():
        assert md1[k] == v

    # the handle does not contain bitsPerValue
    assert md1["bitsPerValue"] == 0
