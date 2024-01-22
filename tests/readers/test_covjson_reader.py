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
from earthkit.data.testing import NO_ECCOVJSON, earthkit_test_data_file


def test_covjson():
    ds = from_source("file", earthkit_test_data_file("time_series.covjson"))
    assert ds


@pytest.mark.skipif(NO_ECCOVJSON, reason="no eccovjson available")
def test_covjson_to_xarray():
    ds = from_source("file", earthkit_test_data_file("time_series.covjson"))
    assert ds
    a = ds.to_xarray()
    assert a


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
