#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.geo import nearest_point_haversine, nearest_point_kdtree


def get_nearest_method(mode):
    if mode == "haversine":
        return nearest_point_haversine
    elif mode == "kdtree":
        return nearest_point_kdtree
    else:
        raise ValueError(f"Invalid mode={mode}")
