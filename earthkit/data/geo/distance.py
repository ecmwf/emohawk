# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np

from earthkit.data.core import constants


def regulate_lat(lat):
    return np.where(np.abs(lat) > constants.north, np.nan, lat)


def haversine_distance(p1, p2):
    """Compute haversine distance between two (sets of) points on Earth.

    Parameters
    ----------
    p1: pair of array-like
        Locations of the first points. The first item specifies the latitudes,
        the second the longitudes (degrees)
    p2: pair of array-like
        Locations of the second points. The first item specifies the latitudes,
        the second the longitudes (degrees)

    Returns
    -------
    number or ndarray
        Spherical distance on the surface in Earth (m)

    Either ``p1`` or ``p2`` must be a single point.

    Examples
    --------
    Compute the distance between Reading and Bologna.
    >>> from earthkit.data.geo import haversine_distance
    >>> p1 = (51.45, -0.97)
    >>> p2 = (44.49, 11.34)
    >>> haversine_distance(p1, p2)
    1196782.5785709629

    Compute the distance from Reading to Bologna and Bonn.
    >>> from earthkit.data.geo import haversine_distance
    >>> p1 = (51.45, -0.97)
    >>> p_lat = [44.49, 50.73]
    >>> p_lon = [11.34, 7.90]
    >>> haversine_distance(p1, (p_lat, p_lon))
    array([1196782.57857096,  624273.19519049])

    """
    lat1 = np.asarray(p1[0])
    lon1 = np.asarray(p1[1])
    lat2 = np.asarray(p2[0])
    lon2 = np.asarray(p2[1])

    if lat1.shape != lon1.shape:
        raise ValueError(
            f"haversine_distance: lat and lon in p1 must have the same shape! {lat1.shape} != {lon1.shape}"
        )

    if lat2.shape != lon2.shape:
        raise ValueError(
            f"haversine_distance: lat and lon in p2 must have the same shape! {lat2.shape} != {lon2.shape}"
        )

    if lat1.size != 1 and lat2.size != 1:
        raise ValueError("haversine_distance: either p1 or p2 must be a single point")

    lat1 = regulate_lat(lat1)
    lat2 = regulate_lat(lat2)

    lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])
    d_lon = lon2 - lon1
    d_lat = lat2 - lat1

    a = np.sqrt(
        np.sin(d_lat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(d_lon / 2) ** 2
    )
    c = 2 * np.arcsin(a)
    distance = constants.R_earth * c

    return distance


def nearest_point_haversine(ref_points, points):
    """Find the index of the nearest point to all ``ref_points`` in a set of ``points`` using the
       haversine distance formula.

    Parameters
    ----------
    ref_points: pair of array-like
        Latitude and longitude coordinates of the reference point (degrees)
    points: pair of array-like
        Locations of the set of points from which the nearest to
        ``ref_points`` is to be found. The first item specifies the latitudes,
        the second the longitudes (degrees)

    Returns
    -------
    ndarray
        Indices of the nearest points to ``ref_points`.
    ndarray
        The distance (m) between the ``ref_points`` and the corresponding nearest
        point in ``points``.

    Examples
    --------
    >>> from earthkit.data.geo import nearest_point_haversine
    >>> p_ref = (51.45, -0.97)
    >>> p_lat = [44.49, 50.73, 50.1]
    >>> p_lon = [11.34, 7.90, -8.1]
    >>> nearest_point_haversine(p_ref, (p_lat, p_lon))
    (array([2]), array([523115.83147777]))

    >>> from earthkit.data.geo import nearest_point_haversine
    >>> p_ref = [(51.45, 41.49, 12.29), (-0.97, 18.34, -17.1)]
    >>> p_lat = [44.49, 50.73, 50.1]
    >>> p_lon = [11.34, 7.90, -8.1]
    >>> nearest_point_haversine(p_ref, (p_lat, p_lon))
    (array([2, 0, 2]), array([ 523115.83147777,  659558.55282001, 4283987.17429322]))

    """
    ref_points = np.asarray(ref_points)
    if ref_points.shape == (2,):
        ref_points = np.array([[ref_points[0]], [ref_points[1]]])
    elif len(ref_points.shape) != 2 or ref_points.shape[0] != 2:
        raise ValueError(
            f"nearest_point_haversine: ref_point expected shape of (2,), got {ref_points.shape}"
        )

    res_index = []
    res_distance = []
    for lat, lon in ref_points.T:
        distance = haversine_distance((lat, lon), points).flatten()
        index = np.nanargmin(distance)
        index = index[0] if isinstance(index, np.ndarray) else index
        res_index.append(index)
        res_distance.append(distance[index])
    return (np.array(res_index), np.array(res_distance))
