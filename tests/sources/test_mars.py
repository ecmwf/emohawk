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
from earthkit.data.testing import NO_MARS


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
@pytest.mark.parametrize("prompt", [True, False])
def test_mars_grib_1_prompt(prompt):
    s = from_source(
        "mars",
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -50, 20, 50],
        grid=[2, 2],
        prompt=prompt,
        date="2023-05-10",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
def test_mars_grib_2():
    s = from_source(
        "mars",
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -50, 20, 50],
        grid=[2, 2],
        date="2023-05-10",
        split_on="param",
    )
    assert len(s) == 2


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
