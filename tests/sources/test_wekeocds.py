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
from earthkit.data.testing import NO_HDA


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_HDA, reason="No access to WEKEO")
@pytest.mark.parametrize("prompt", [True, False])
def test_wekeo_grib_1_prompt(prompt):
    s = from_source(
        "wekeocds",
        "EO:ECMWF:DAT:REANALYSIS_ERA5_SINGLE_LEVELS",
        variable=["2m_temperature", "mean_sea_level_pressure"],
        product_type=["reanalysis"],
        year=["2012"],
        month=["12"],
        day=["12"],
        time=["13:00"],
        prompt=prompt,
        format="grib",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_HDA, reason="No access to CDS")
def test_wekeo_grib_2():
    s = from_source(
        "wekeocds",
        "EO:ECMWF:DAT:REANALYSIS_ERA5_SINGLE_LEVELS",
        variable=["2m_temperature", "mean_sea_level_pressure"],
        product_type=["reanalysis"],
        year=["2012"],
        month=["12"],
        day=["12"],
        time=["13:00"],
        format="grib",
        split_on="variable",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_HDA, reason="No access to CDS")
def test_wekeo_grib_3():
    s = from_source(
        "wekeocds",
        "EO:ECMWF:DAT:REANALYSIS_ERA5_SINGLE_LEVELS",
        variable=["2m_temperature", "mean_sea_level_pressure"],
        product_type=["reanalysis"],
        year=["2012"],
        month=["12"],
        day=["12", "13", "14", "15"],
        time=["13:00"],
        format="grib",
    )
    assert len(s) == 8


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_HDA, reason="No access to CDS")
def test_wekeo_netcdf():
    s = from_source(
        "wekeocds",
        "EO:ECMWF:DAT:REANALYSIS_ERA5_SINGLE_LEVELS",
        variable=["2m_temperature", "mean_sea_level_pressure"],
        product_type=["reanalysis"],
        year=["2012"],
        month=["12"],
        day=["12"],
        time=["13:00"],
        format="netcdf",
    )
    assert len(s) == 2


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
