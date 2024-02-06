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
import sqlite3

import pytest

import earthkit.data
from earthkit.data.core.temporary import temp_directory


def _make_db(path):
    DATA = [
        (50, 3.3, "2001-01-01 00:00:00", 4.9),
        (51, -3, "2001-01-02 00:00:00", 7.3),
        (50.5, -1.8, "2001-01-03 00:00:00", 5.5),
    ]
    if os.path.exists(path):
        os.unlink(path)

    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE data(
                    lat NUMBER,
                    lon NUMBER,
                    time TEXT,
                    value NUMBER)"""
    )
    c.executemany("INSERT INTO data VALUES(?,?,?,?);", DATA)
    conn.commit()


@pytest.mark.plugin
def test_demo_source_plugin():
    with temp_directory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.db")

        _make_db(path)

        ds = earthkit.data.from_source(
            "demo-source",
            f"sqlite:///{path}",
            "select * from data;",
            parse_dates=["time"],
        )

        df = ds.to_pandas()
        assert len(df) == 3
        assert list(df.columns) == ["lat", "lon", "time", "value"]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
