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
from earthkit.data.utils.serialise import (
    SERIALISATION,
    deserialise_state,
    serialise_state,
)

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from indexing_fixtures import get_tmp_fixture  # noqa E402


# TODO: add test for mode=multi
@pytest.mark.cache
@pytest.mark.parametrize("mode", ["file", "directory"])
@pytest.mark.parametrize("params", (["t", "u"], ["u", "t"]))
@pytest.mark.parametrize("levels", ([500, 850], [850, 500]))
def test_indexing_pickle(mode, params, levels):
    tmp, path = get_tmp_fixture(mode)
    ds = from_source("file", path, indexing=True)

    request = dict(
        level=levels,
        variable=params,
        date=20180801,
        time="1200",
    )

    ds = ds.sel(**request)
    ds = ds.order_by(["level", "param"])

    assert len(ds) == 4, (len(ds), ds, SERIALISATION)
    state = serialise_state(ds)
    ds = deserialise_state(state)
    assert len(ds) == 4, (len(ds), ds, SERIALISATION)

    ref = dict(shortName=["t", "u", "t", "u"], level=[500, 500, 850, 850])

    for k, v in ref.items():
        assert ds.metadata(k) == v


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
