#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data import from_source
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.testing import earthkit_examples_file, earthkit_test_data_file


def load_numpy_fieldlist(path):
    ds = from_source("file", path)
    return FieldList.from_numpy(
        ds.values, [m.override(generatingProcessIdentifier=120) for m in ds.metadata()]
    )


def load_file_or_numpy_fs(filename, mode, folder="example"):
    if folder == "example":
        path = earthkit_examples_file(filename)
    elif folder == "data":
        path = earthkit_test_data_file(filename)
    else:
        raise ValueError("Invalid folder={folder}")

    if mode == "file":
        return from_source("file", path)
    else:
        return load_numpy_fieldlist(path)
