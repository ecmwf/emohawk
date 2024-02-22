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

NO_ADS = not os.path.exists(os.path.expanduser("~/.adsapirc"))


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_ADS, reason="No access to ADS")
@pytest.mark.parametrize("prompt", [True, False])
def test_ads_grib_1_prompt(prompt):
    s = from_source(
        "ads",
        "cams-global-reanalysis-eac4",
        variable=["particulate_matter_10um", "particulate_matter_1um"],
        area=[50, -50, 20, 50],
        date="2012-12-12",
        prompt=prompt,
        time="12:00",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_ADS, reason="No access to ADS")
def test_ads_grib_2():
    s = from_source(
        "ads",
        "cams-global-reanalysis-eac4",
        variable=["particulate_matter_10um", "particulate_matter_1um"],
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
        split_on="variable",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_ADS, reason="No access to ADS")
def test_ads_grib_3():
    s = from_source(
        "ads",
        "cams-global-reanalysis-eac4",
        variable=["particulate_matter_10um", "particulate_matter_1um"],
        area=[50, -50, 20, 50],
        date="2012-12-12/to/2012-12-15",
        time="12:00",
    )
    assert len(s) == 8


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_ADS, reason="No access to ADS")
def test_ads_netcdf():
    s = from_source(
        "ads",
        "cams-global-reanalysis-eac4",
        variable=["particulate_matter_10um", "particulate_matter_1um"],
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
        format="netcdf",
    )
    assert len(s) == 2


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
