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

import pytest

from earthkit.data import from_source

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from indexing_fixtures import get_tmp_fixture  # noqa: E402


@pytest.mark.cache
def test_indexing_db_file():
    tmp, path = get_tmp_fixture("file")
    ds = from_source("file", path, indexing=True)
    assert hasattr(ds, "db")
    assert ds.db.count() == 18


@pytest.mark.cache
def test_indexing_db_file_multi():
    tmp, path = get_tmp_fixture("multi")
    ds = from_source("file", path, indexing=True)

    counts = [6, 6, 6]
    assert len(counts) == len(ds._indexes)
    for i, d in enumerate(ds._indexes):
        assert hasattr(d, "db"), f"db,{i}"
        assert d.db.count() == counts[i]


@pytest.mark.cache
def test_indexing_db_directory():
    tmp, path = get_tmp_fixture("directory")
    ds = from_source("file", path, indexing=True)
    assert hasattr(ds, "db")
    assert ds.db.count() == 18


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
