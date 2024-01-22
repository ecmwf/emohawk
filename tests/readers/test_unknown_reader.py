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

import earthkit.data


def test_unknown_reader():
    s = earthkit.data.from_source(
        "file",
        os.path.join(os.path.dirname(__file__), "unknown_file.unknown_ext"),
    )
    print(s)
    assert isinstance(s._reader, earthkit.data.readers.unknown.UnknownReader)


def test_text_reader():
    s = earthkit.data.from_source(
        "file",
        os.path.join(os.path.dirname(__file__), "unknown_text_file.unknown_ext"),
    )
    print(s)
    assert isinstance(s._reader, earthkit.data.readers.text.TextReader)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
