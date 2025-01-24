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

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.encoders.grib import GribEncoder
from earthkit.data.targets import to_target
from earthkit.data.targets.fdb import FDBTarget
from earthkit.data.testing import NO_FDB
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file

TEST_GRIB_REQUEST = {
    "class": "od",
    "expver": "0001",
    "stream": "oper",
    "date": "20200513",
    "time": 1200,
    "domain": "g",
    "type": "an",
    "levtype": "sfc",
    "step": 0,
    "param": [167, 151],
}


def make_fdb_config(path):
    fdb_schema = earthkit_test_data_file("fdb_schema.txt")
    fdb_dir = path
    os.makedirs(fdb_dir, exist_ok=True)
    config = {
        "type": "local",
        "engine": "toc",
        "schema": fdb_schema,
        "spaces": [{"handler": "Default", "roots": [{"path": fdb_dir}]}],
    }
    return config


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"encoder": "grib"},
        {"encoder": GribEncoder()},
    ],
)
@pytest.mark.parametrize("direct_call", [True, False])
def test_target_fdb_grib_core(kwargs, direct_call):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_directory() as tmpdir:
        config = make_fdb_config(os.path.join(tmpdir, "_fdb"))

        if direct_call:
            to_target("fdb", config=config, data=ds, **kwargs)
        else:
            ds.to_target("fdb", config=config, **kwargs)

        # target = FDBTarget(config=config)
        # if per_field:
        #     target.write(ds[0])
        #     target.write(ds[1])
        # else:
        #     target.write(ds)

        # target.flush()

        ds1 = from_source("fdb", TEST_GRIB_REQUEST, config=config, stream=False)
        assert len(ds) == len(ds1)
        assert ds1.metadata("shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)


@pytest.mark.skipif(NO_FDB, reason="No access to FDB")
@pytest.mark.parametrize("per_field", [True, False])
def test_target_fdb_grib_direct_api(per_field):
    ds = from_source("file", earthkit_examples_file("test.grib"))
    vals_ref = ds.values[:, :4]

    with temp_directory() as tmpdir:
        config = make_fdb_config(os.path.join(tmpdir, "_fdb"))

        target = FDBTarget(config=config)
        if per_field:
            target.write(ds[0])
            target.write(ds[1])
        else:
            target.write(ds)

        target.flush()

        ds1 = from_source("fdb", TEST_GRIB_REQUEST, config=config, stream=False)
        assert len(ds) == len(ds1)
        assert ds1.metadata("shortName") == ["2t", "msl"]
        assert np.allclose(ds1.values[:, :4], vals_ref)
