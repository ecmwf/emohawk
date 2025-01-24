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
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import write_to_file


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_netcdf_fieldlist_save(write_method):
    ds = from_source("file", earthkit_examples_file("test.nc"))

    # the file must be saved without loading the fields
    # assert ds._reader._fields is None
    assert ds._fields is None

    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)
        # assert ds._reader._fields is None
        assert ds._fields is None
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        assert len(r_tmp) == 2


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_netcdf_fieldlist_subset_save_1(write_method):
    ds = from_source("file", earthkit_examples_file("test.nc"))
    assert len(ds) == 2
    r = ds[1]

    tmp = temp_file()
    with pytest.raises(NotImplementedError):
        write_to_file(write_method, tmp.path, r)


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_netcdf_fieldlist_subset_save_2(write_method):
    ds = from_source("file", earthkit_examples_file("tuv_pl.nc"))
    assert len(ds) == 18
    r = ds[1:4]

    tmp = temp_file()
    with pytest.raises(NotImplementedError):
        write_to_file(write_method, tmp.path, r)


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_netcdf_fieldlist_multi_subset_save(write_method):
    ds1 = from_source("file", earthkit_examples_file("test.nc"))
    ds2 = from_source("file", earthkit_examples_file("tuv_pl.nc"))

    ds = ds1 + ds2
    assert len(ds) == 20

    tmp = temp_file()
    write_to_file(write_method, tmp.path, ds)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == 20


@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_netcdf_fieldlist_multi_subset_save_bad(write_method):
    ds1 = from_source("file", earthkit_examples_file("test.nc"))
    ds2 = from_source("file", earthkit_examples_file("tuv_pl.nc"))

    ds = ds1 + ds2[1:5]
    assert len(ds) == 6

    tmp = temp_file()
    with pytest.raises(NotImplementedError):
        write_to_file(write_method, tmp.path, ds)
