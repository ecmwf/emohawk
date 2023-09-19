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

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_file_or_numpy_fs  # noqa: E402


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "index,expected_meta",
    [
        (0, ["t", 1000]),
        (2, ["v", 1000]),
        (17, ["v", 300]),
        (-1, ["v", 300]),
        (-5, ["u", 400]),
    ],
)
def test_grib_single_index(mode, index, expected_meta):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)
    # f = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    r = f[index]
    assert r.metadata(["shortName", "level"]) == expected_meta
    v = r.values
    assert v.shape == (84,)
    # eps = 0.001
    # assert np.isclose(v[1088], 304.5642, eps)


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_single_index_bad(mode):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)
    with pytest.raises(IndexError):
        f[27]


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "indexes,expected_meta",
    [
        (slice(0, 4), [["t", 1000], ["u", 1000], ["v", 1000], ["t", 850]]),
        (slice(None, 4), [["t", 1000], ["u", 1000], ["v", 1000], ["t", 850]]),
        (slice(2, 9, 2), [["v", 1000], ["u", 850], ["t", 700], ["v", 700]]),
        (slice(8, 1, -2), [["v", 700], ["t", 700], ["u", 850], ["v", 1000]]),
        (slice(14, 18), [["v", 400], ["t", 300], ["u", 300], ["v", 300]]),
        (slice(14, None), [["v", 400], ["t", 300], ["u", 300], ["v", 300]]),
    ],
)
def test_grib_slice_single_file(mode, indexes, expected_meta):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)
    r = f[indexes]
    assert len(r) == 4
    assert r.metadata(["shortName", "level"]) == expected_meta
    v = r.values
    assert v.shape == (4, 84)
    # check the original fieldlist
    assert len(f) == 18
    assert f.metadata("shortName") == ["t", "u", "v"] * 6


@pytest.mark.parametrize(
    "indexes,expected_meta",
    [
        (slice(1, 4), [["msl", 0], ["t", 500], ["z", 500]]),
        (slice(1, 6, 2), [["msl", 0], ["z", 500], ["z", 850]]),
        (slice(5, 0, -2), [["z", 850], ["z", 500], ["msl", 0]]),
        (slice(3, 6), [["z", 500], ["t", 850], ["z", 850]]),
    ],
)
def test_grib_slice_multi_file(indexes, expected_meta):
    f = from_source(
        "file",
        [earthkit_examples_file("test.grib"), earthkit_examples_file("test4.grib")],
    )
    r = f[indexes]
    assert len(r) == 3
    assert r.metadata(["shortName", "level"]) == expected_meta
    # v = r.values
    # assert v.shape == (3, 84)
    # check the original fieldlist
    assert len(f) == 6
    assert f.metadata("shortName") == ["2t", "msl", "t", "z", "t", "z"]


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize(
    "indexes1,indexes2",
    [(np.array([1, 16, 5, 9]), np.array([1, 3])), ([1, 16, 5, 9], [1, 3])],
)
def test_grib_array_indexing(mode, indexes1, indexes2):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)

    r = f[indexes1]
    assert len(r) == 4
    assert r.metadata("shortName") == ["u", "u", "v", "t"]

    r1 = r[indexes2]
    assert len(r1) == 2
    assert r1.metadata("shortName") == ["u", "t"]


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
@pytest.mark.parametrize("indexes", [(np.array([1, 19, 5, 9])), ([1, 19, 5, 9])])
def test_grib_array_indexing_bad(mode, indexes):
    f = load_file_or_numpy_fs("tuv_pl.grib", mode)
    with pytest.raises(IndexError):
        f[indexes]


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_fieldlist_iterator(mode):
    g = load_file_or_numpy_fs("tuv_pl.grib", mode)
    sn = g.metadata("shortName")
    assert len(sn) == 18
    iter_sn = [f.metadata("shortName") for f in g]
    assert iter_sn == sn
    # repeated iteration
    iter_sn = [f.metadata("shortName") for f in g]
    assert iter_sn == sn


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_fieldlist_iterator_with_zip(mode):
    # test something different to the iterator - does not try to
    # 'go off the edge' of the fieldlist, because the length is determined by
    # the list of levels
    g = load_file_or_numpy_fs("tuv_pl.grib", mode)
    ref_levs = g.metadata("level")
    assert len(ref_levs) == 18
    levs1 = []
    levs2 = []
    for k, f in zip(g.metadata("level"), g):
        levs1.append(k)
        levs2.append(f.metadata("level"))
    assert levs1 == ref_levs
    assert levs2 == ref_levs


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_fieldlist_iterator_with_zip_multiple(mode):
    # same as test_fieldlist_iterator_with_zip() but multiple times
    g = load_file_or_numpy_fs("tuv_pl.grib", mode)
    ref_levs = g.metadata("level")
    assert len(ref_levs) == 18
    for i in range(2):
        levs1 = []
        levs2 = []
        for k, f in zip(g.metadata("level"), g):
            levs1.append(k)
            levs2.append(f.metadata("level"))
        assert levs1 == ref_levs, i
        assert levs2 == ref_levs, i


@pytest.mark.parametrize("mode", ["file", "numpy_fs"])
def test_grib_fieldlist_reverse_iterator(mode):
    g = load_file_or_numpy_fs("tuv_pl.grib", mode)
    sn = g.metadata("shortName")
    sn_reversed = list(reversed(sn))
    assert sn_reversed[0] == "v"
    assert sn_reversed[17] == "t"
    gr = reversed(g)
    iter_sn = [f.metadata("shortName") for f in gr]
    assert len(iter_sn) == len(sn_reversed)
    assert iter_sn == sn_reversed
    assert iter_sn == ["v", "u", "t"] * 6
