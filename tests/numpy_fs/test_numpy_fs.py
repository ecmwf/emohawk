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

import numpy as np

from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file

LOG = logging.getLogger(__name__)


def test_numpy_list_grib_single_field():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    lat, lon, v = ds[0].data(flatten=True)
    v1 = v + 1

    md = ds[0].metadata()
    md1 = md.override(shortName="msl")
    r = FieldList.from_numpy(v1, md1)

    def _check_field(r):
        assert len(r) == 1
        assert np.allclose(r[0].values, v1)
        assert r[0].shape == ds[0].shape
        assert r[0].metadata("shortName") == "msl"
        _lat, _lon, _v = r[0].data(flatten=True)
        assert np.allclose(_lat, lat)
        assert np.allclose(_lon, lon)
        assert np.allclose(_v, v1)

    _check_field(r)

    # save to disk
    tmp = temp_file()
    r.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    _check_field(r_tmp)


def test_numpy_list_grib_multi_field():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds[0].metadata("shortName") == "2t"

    v = ds.values
    v1 = v + 1

    md1 = [f.metadata().override(shortName="2d") for f in ds]
    r = FieldList.from_numpy(v1, md1)

    assert len(r) == 2
    assert np.allclose(v1, r.values)
    for i, f in enumerate(r):
        assert f.shape == ds[i].shape
        assert f.metadata("shortName") == "2d", f"shortName {i}"
        assert f.metadata("name") == "2 metre dewpoint temperature", f"name {i}"

    # save to disk
    tmp = temp_file()
    r.save(tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 2
    assert np.allclose(v1, r_tmp.values)
    for i, f in enumerate(r_tmp):
        assert f.shape == ds[i].shape
        assert f.metadata("shortName") == "2d", f"shortName {i}"
        assert f.metadata("name") == "2 metre dewpoint temperature", f"name {i}"


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
