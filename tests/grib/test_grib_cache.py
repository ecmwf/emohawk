#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data import from_source
from earthkit.data import settings
from earthkit.data.testing import earthkit_examples_file


@pytest.mark.parametrize("handle_cache_size", [1, 5])
def test_grib_cache_basic(handle_cache_size):

    with settings.temporary(
        {
            "store-grib-fields-in-memory": True,
            "grib-handle-cache-size": handle_cache_size,
            "use-grib-metadata-cache": True,
        }
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._caches
        assert cache

        # unique values
        ref_vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        diag = ds._diag()
        ref = {
            "field_cache_size": 18,
            "field_cache_create_count": 18,
            "handle_cache_size": handle_cache_size,
            "handle_cache_create_count": 18,
            "handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        for i, f in enumerate(ds):
            assert i in cache.field_cache, f"{i} not in cache"
            assert id(f) == id(cache.field_cache[i]), f"{i} not the same object"

        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        # unique values repeated
        vals = ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert vals == ref_vals
        diag = ds._diag()
        ref = {
            "field_cache_size": 18,
            "field_cache_create_count": 18,
            "handle_cache_size": handle_cache_size,
            "handle_cache_create_count": 18,
            "handle_count": 0,
            "metadata_cache_hits": 18 * 4,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }
        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        # order by
        ds.order_by(["levelist", "valid_datetime", "paramId", "levtype"])
        diag = ds._diag()
        ref = {
            "field_cache_size": 18,
            "field_cache_create_count": 18,
            "handle_cache_size": handle_cache_size,
            "handle_cache_create_count": 18,
            "handle_count": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }

        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        assert diag["metadata_cache_hits"] >= 18 * 4

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0].handle == md._handle


def test_grib_cache_no_handle_1():
    with settings.temporary(
        {"store-grib-fields-in-memory": True, "grib-handle-cache-size": 0, "use-grib-metadata-cache": True}
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._caches
        assert cache

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert cache.handle_cache is None

        diag = ds._diag()
        ref = {
            "field_cache_size": 18,
            "field_cache_create_count": 18,
            "handle_cache_size": 0,
            "handle_cache_create_count": 0,
            "handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 18 * 6,
            "metadata_cache_size": 18 * 6,
        }

        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        for i, f in enumerate(ds):
            assert i in cache.field_cache, f"{i} not in cache"
            assert id(f) == id(cache.field_cache[i]), f"{i} not the same object"

        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle is None


def test_grib_cache_no_handle_2():
    with settings.temporary(
        {"store-grib-fields-in-memory": False, "grib-handle-cache-size": 0, "use-grib-metadata-cache": True}
    ):
        ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))
        assert len(ds) == 18

        cache = ds._caches
        assert cache

        # unique values
        ds.unique_values("paramId", "levelist", "levtype", "valid_datetime")

        assert cache.handle_cache is None

        diag = ds._diag()
        ref = {
            "field_cache_size": 0,
            "field_cache_create_count": 0,
            "handle_cache_size": 0,
            "handle_cache_create_count": 0,
            "handle_count": 0,
            "metadata_cache_hits": 0,
            "metadata_cache_misses": 0,
            "metadata_cache_size": 0,
        }

        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        assert cache.field_cache is None
        assert cache.handle_cache is None

        # metadata object is not decoupled from the field object
        md = ds[0].metadata()
        assert hasattr(md, "_field")
        assert ds[0]._handle != md._handle

        # keep a reference to the field
        first = ds[0]
        md = first.metadata()
        assert md._field == first
        assert first._handle is None

        v = first.metadata("levelist")
        v = first.metadata("levelist")

        assert first.handle == md._handle

        diag = ds._diag()
        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"

        diag = first._diag()
        ref = {
            "metadata_cache_hits": 1,
            "metadata_cache_misses": 1,
            "metadata_cache_size": 1,
        }

        for k, v in ref.items():
            assert diag[k] == v, f"{k}={diag[k]} != {v}"