#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime

import pytest

from earthkit.data import from_source
from earthkit.data.testing import NO_FDB


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
def test_fdb_grib_stream():
    d = datetime.datetime.now() - datetime.timedelta(days=2)
    request = {
        "class": "od",
        "expver": "0001",
        "stream": "oper",
        "date": d.strftime("%Y%m%d"),
        "time": [0, 12],
        "domain": "g",
        "type": "an",
        "levtype": "sfc",
        "step": 0,
        "param": [151, 167],
    }

    ds = from_source("fdb", request)
    cnt = sum([1 for f in ds])
    assert cnt == 4


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
def test_fdb_grib_file():
    d = datetime.datetime.now() - datetime.timedelta(days=2)
    request = {
        "class": "od",
        "expver": "0001",
        "stream": "oper",
        "date": d.strftime("%Y%m%d"),
        "time": [0, 12],
        "domain": "g",
        "type": "an",
        "levtype": "sfc",
        "step": 0,
        "param": [151, 167],
    }

    ds = from_source("fdb", request, stream=False)
    assert len(ds) == 4


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
