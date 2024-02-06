# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import math
from abc import abstractmethod
from collections import defaultdict

from earthkit.data.core import Base
from earthkit.data.core.index import Index
from earthkit.data.decorators import cached_method
from earthkit.data.utils.metadata import metadata_argument


class Field(Base):
    r"""Represents a Field."""

    def __init__(self, metadata=None):
        self.__metadata = metadata

    @abstractmethod
    def _values(self, dtype=None):
        r"""Return the values stored in the field as an ndarray.

        Parameters
        ----------
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``np.float64``.

        Returns
        -------
        ndarray
            Field values

        """
        self._not_implemented()

    @property
    def values(self):
        r"""ndarray: Get the values stored in the field as a 1D ndarray."""
        v = self._values()
        if len(v.shape) != 1:
            n = math.prod(v.shape)
            return v.reshape(n)
        return v

    def _make_metadata(self):
        r"""Create a field metadata object."""
        self._not_implemented()

    @property
    def _metadata(self):
        r"""Metadata: Get the object representing the field's metadata."""
        if self.__metadata is None:
            self.__metadata = self._make_metadata()
        return self.__metadata

    def to_numpy(self, flatten=False, dtype=None):
        r"""Return the values stored in the field as an ndarray.

        Parameters
        ----------
        flatten: bool
            When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``np.float64``.

        Returns
        -------
        ndarray
            Field values

        """
        v = self._values(dtype=dtype)
        shape = self._required_shape(flatten)
        if shape != v.shape:
            return v.reshape(shape)
        return v

    def _required_shape(self, flatten):
        return self.shape if not flatten else (math.prod(self.shape),)

    def _array_matches(self, array, flatten=False, dtype=None):
        shape = self._required_shape(flatten)
        return shape == array.shape and (dtype is None or dtype == array.dtype)

    def data(self, keys=("lat", "lon", "value"), flatten=False, dtype=None):
        r"""Return the values and/or the geographical coordinates for each grid point.

        Parameters
        ----------
        keys: :obj:`str`, :obj:`list` or :obj:`tuple`
            Specifies the type of data to be returned. Any combination of "lat", "lon" and "value"
            is allowed here.
        flatten: bool
            When it is True a flat ndarray per key is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned for each key.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``np.float64``.


        Returns
        -------
        ndarray
            An ndarray containing one ndarray per key is returned
            (following the order in ``keys``). When ``keys`` is a single value only the
            ndarray belonging to the key is returned.


        Examples
        --------
        - :ref:`/examples/grib_lat_lon_value.ipynb`

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
        >>> d = ds[0].data()
        >>> d.shape
        (3, 7, 12)
        >>> d[0, 0, 0]  # first latitude
        90.0
        >>> d[1, 0, 0]  # first longitude
        0.0
        >>> d[2, 0, 0]  # first value
        272.56417847
        >>> d = ds[0].data(keys="lon")
        >>> d.shape
        (7, 12)
        >>> d[0, 0]  # first longitude
        0.0

        See Also
        --------
        to_latlon
        to_points
        to_numpy
        values

        """
        _keys = dict(
            lat=self._metadata.geography.latitudes,
            lon=self._metadata.geography.longitudes,
            value=self._values,
        )

        if isinstance(keys, str):
            keys = [keys]

        for k in keys:
            if k not in _keys:
                raise ValueError(f"data: invalid argument: {k}")

        r = [_keys[k](dtype=dtype) for k in keys]
        shape = self._required_shape(flatten)
        if shape != r[0].shape:
            r = [x.reshape(shape) for x in r]

        if len(r) == 1:
            return r[0]
        else:
            import numpy as np

            return np.array(r)

    def to_points(self, flatten=False, dtype=None):
        r"""Return the geographical coordinates in the data's original
        Coordinate Reference System (CRS).

        Parameters
        ----------
        flatten: bool
            When it is True 1D ndarrays are returned. Otherwise ndarrays with the field's
            :obj:`shape` are returned.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``np.float64``.

        Returns
        -------
        dict
            Dictionary with items "x" and "y", containing the ndarrays of the x and
            y coordinates, respectively.

        Raises
        ------
        ValueError
            When the coordinates in the data's original CRS are not available.

        See Also
        --------
        to_latlon

        """
        x = self._metadata.geography.x(dtype=dtype)
        y = self._metadata.geography.y(dtype=dtype)
        if x is not None and y is not None:
            shape = self._required_shape(flatten)
            if shape != x.shape:
                x = x.reshape(shape)
                y = y.reshape(shape)
            return dict(x=x, y=y)
        elif self.projection().CARTOPY_CRS == "PlateCarree":
            lon, lat = self.data(("lon", "lat"), flatten=flatten, dtype=dtype)
            return dict(x=lon, y=lat)
        else:
            raise ValueError(
                "to_points(): geographical coordinates in original CRS are not available"
            )

    def to_latlon(self, flatten=False, dtype=None):
        r"""Return the latitudes/longitudes of all the gridpoints in the field.

        Parameters
        ----------
        flatten: bool
            When it is True 1D ndarrays are returned. Otherwise ndarrays with the field's
            :obj:`shape` are returned.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``np.float64``.

        Returns
        -------
        dict
            Dictionary with items "lat" and "lon", containing the ndarrays of the latitudes and
            longitudes, respectively.

        See Also
        --------
        to_points

        """
        lon, lat = self.data(("lon", "lat"), flatten=flatten, dtype=dtype)
        return dict(lat=lat, lon=lon)

    @property
    def shape(self):
        r"""tuple: Get the shape of the field.

        For structured grids the shape is a tuple in the form of (Nj, Ni) where:

        - ni: the number of gridpoints in i direction (longitude for a regular latitude-longitude grid)
        - nj: the number of gridpoints in j direction (latitude for a regular latitude-longitude grid)

        For other grid types the number of gridpoints is returned as ``(num,)``
        """
        return self._metadata.geography.shape()

    def projection(self):
        r"""Return information about the projection.

        Returns
        -------
        :obj:`Projection`

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.projection()
        <Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to ...>
        Name: unknown
        Axis Info [cartesian]:
        - E[east]: Easting (unknown)
        - N[north]: Northing (unknown)
        - h[up]: Ellipsoidal height (metre)
        Area of Use:
        - undefined
        Coordinate Operation:
        - name: unknown
        - method: Equidistant Cylindrical
        Datum: Unknown based on WGS 84 ellipsoid
        - Ellipsoid: WGS 84
        - Prime Meridian: Greenwich
        >>> ds.projection().to_proj_string()
        '+proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to_meter=111319.4907932736 +no_defs +type=crs'
        """
        return self._metadata.geography.projection()

    def bounding_box(self):
        r"""Return the bounding box of the field.

        Returns
        -------
        :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
        """
        return self._metadata.geography.bounding_box()

    def datetime(self):
        r"""Return the date and time of the field.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".


        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
        >>> ds[4].datetime()
        {'base_time': datetime.datetime(2020, 12, 21, 12, 0),
        'valid_time': datetime.datetime(2020, 12, 21, 18, 0)}

        """
        return self._metadata.datetime()

    def metadata(self, *keys, astype=None, **kwargs):
        r"""Return metadata values from the field.

        When called without any arguments returns a :obj:`Metadata` object.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying metadata keys. Can be empty, in this case all
            the keys from the specified ``namespace`` will
            be used. (See examples below).
        astype: type name, :obj:`list` or :obj:`tuple`
            Return types for ``keys``. A single value is accepted and applied to all the ``keys``.
            Otherwise, must have same the number of elements as ``keys``. Only used when
            ``keys`` is not empty.
        **kwargs: dict, optional
            Other keyword arguments:

            * namespace: :obj:`str`, :obj:`list`, :obj:`tuple`, :obj:`None` or :obj:`all`
                The namespace to choose the ``keys`` from. When ``keys`` is empty and ``namespace`` is
                :obj:`all` all the available namespaces will be used. When ``keys`` is non empty
                ``namespace`` cannot specify multiple values and it cannot be :obj:`all`. When
                ``namespace`` is None or empty str all the available keys will be used
                (without a namespace qualifier).

            * default: value, optional
                Specifies the same default value for all the ``keys`` specified. When ``default`` is
                **not present** and a key is not found or its value is a missing value
                :obj:`metadata` will raise KeyError.

        Returns
        -------
        single value, :obj:`list`, :obj:`tuple`, :obj:`dict` or :obj:`Metadata`
            - when called without any arguments returns a :obj:`Metadata` object
            - when ``keys`` is not empty:
                - returns single value when ``keys`` is a str
                - otherwise returns the same type as that of ``keys`` (:obj:`list` or :obj:`tuple`)
            - when ``keys`` is empty:
                - when ``namespace`` is None or an empty str returns a :obj:`dict` with all
                  the available keys and values
                - when ``namespace`` is :obj:`str` returns a :obj:`dict` with the keys and values
                  in that namespace
                - otherwise returns a :obj:`dict` with one item per namespace (dict of dict)

        Raises
        ------
        KeyError
            If no ``default`` is set and a key is not found in the message or it has a missing value.


        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")

        Calling without arguments:

        >>> r = ds[0].metadata()
        >>> r
        <earthkit.data.readers.grib.metadata.GribMetadata object at 0x164ace170>
        >>> r["name"]
        '2 metre temperature'

        Getting keys with their native type:

        >>> ds[0].metadata("param")
        '2t'
        >>> ds[0].metadata("param", "units")
        ('2t', 'K')
        >>> ds[0].metadata(("param", "units"))
        ('2t', 'K')
        >>> ds[0].metadata(["param", "units"])
        ['2t', 'K']
        >>> ds[0].metadata(["param"])
        ['2t']
        >>> ds[0].metadata("badkey")
        KeyError: 'badkey'
        >>> ds[0].metadata("badkey", default=None)
        <BLANKLINE>

        Prescribing key types:

        >>> ds[0].metadata("centre", astype=int)
        98
        >>> ds[0].metadata(["paramId", "centre"], astype=int)
        [167, 98]
        >>> ds[0].metadata(["centre", "centre"], astype=[int, str])
        [98, 'ecmf']

        Using namespaces:

        >>> ds[0].metadata(namespace="parameter")
        {'centre': 'ecmf', 'paramId': 167, 'units': 'K', 'name': '2 metre temperature', 'shortName': '2t'}
        >>> ds[0].metadata(namespace=["parameter", "vertical"])
        {'parameter': {'centre': 'ecmf', 'paramId': 167, 'units': 'K', 'name': '2 metre temperature',
         'shortName': '2t'},
         'vertical': {'typeOfLevel': 'surface', 'level': 0}}
        >>> r = ds[0].metadata(namespace=all)
        >>> r.keys()
        dict_keys(['default', 'ls', 'geography', 'mars', 'parameter', 'statistics', 'time', 'vertical'])
        >>> r = ds[0].metadata(namespace=None)
        >>> len(r)
        186
        >>> r["name"]
        '2 metre temperature'
        """
        # when called without arguments returns the metadata object
        if len(keys) == 0 and astype is None and len(kwargs) == 0:
            return self._metadata

        namespace = kwargs.pop("namespace", None)
        key, namespace, astype, key_arg_type = metadata_argument(
            *keys, namespace=namespace, astype=astype
        )

        assert isinstance(key, list)
        assert isinstance(namespace, (list, tuple))

        if key:
            assert isinstance(astype, (list, tuple))
            if namespace and namespace[0] != "default":
                key = [namespace[0] + "." + k for k in key]

            raise_on_missing = "default" not in kwargs
            default = kwargs.pop("default", None)

            r = [
                self._metadata.get(
                    k,
                    default=default,
                    astype=kt,
                    raise_on_missing=raise_on_missing,
                    **kwargs,
                )
                for k, kt in zip(key, astype)
            ]

            if key_arg_type == str:
                return r[0]
            elif key_arg_type == tuple:
                return tuple(r)
            else:
                return r
        elif namespace:
            if all in namespace:
                namespace = self._metadata.namespaces()

            r = {ns: self._metadata.as_namespace(ns) for ns in namespace}
            if len(r) == 1:
                return r[namespace[0]]
            else:
                return r
        else:
            return self._metadata.as_namespace(None)

    def dump(self, namespace=all, **kwargs):
        r"""Generate dump with all the metadata keys belonging to ``namespace``.

        In a Jupyter notebook it is represented as a tabbed interface.

        Parameters
        ----------
        namespace: :obj:`str`, :obj:`list`, :obj:`tuple`, :obj:`None` or :obj:`all`
            The namespace to dump. The following `namespace` values
            have a special meaning:

            - :obj:`all`: all the available namespaces will be used.
            - None or empty str: all the available keys will be used
                (without a namespace qualifier)

        **kwargs: dict, optional
            Other keyword arguments used for testing only

        Returns
        -------
        NamespaceDump
            Dict-like object with one item per namespace. In a Jupyter notebook represented
            as a tabbed interface to browse the dump contents.

        Examples
        --------
        :ref:`/examples/grib_metadata.ipynb`

        """
        return self._metadata.dump(namespace=namespace, **kwargs)

    def __getitem__(self, key):
        """Return the value of the metadata ``key``."""
        return self._metadata.get(key)

    @abstractmethod
    def message(self):
        r"""Return a buffer containing the encoded message for message based formats (e.g. GRIB).

        Returns
        -------
        bytes
        """
        self._not_implemented()

    def __repr__(self):
        return "%s(%s,%s,%s,%s,%s,%s)" % (
            self.__class__.__name__,
            self._metadata.get("shortName", None),
            self._metadata.get("levelist", None),
            self._metadata.get("date", None),
            self._metadata.get("time", None),
            self._metadata.get("step", None),
            self._metadata.get("number", None),
        )

    @abstractmethod
    def _attributes(self, names):
        result = {}
        for name in names:
            result[name] = self._metadata.get(name, None)
        return result


class FieldList(Index):
    r"""Represents a list of :obj:`Field` \s."""

    _md_indices = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def from_numpy(array, metadata):
        from earthkit.data.sources.numpy_list import NumpyFieldList

        return NumpyFieldList(array, metadata)

    def ignore(self):
        # When the concrete type is Fieldlist we assume the object was
        # created with Fieldlist() i.e. it is empty. We ignore it from
        # all the merge operations.
        if type(self) is FieldList:
            return True
        else:
            return False

    @cached_method
    def _default_index_keys(self):
        if len(self) > 0:
            return self[0].metadata().index_keys()
        else:
            return []

    def _find_index_values(self, key):
        values = set()
        for f in self:
            v = f.metadata(key, default=None)
            if v is not None:
                values.add(v)
        return sorted(list(values))

    def _find_all_index_dict(self):
        indices = defaultdict(set)
        for f in self:
            for k in self._default_index_keys():
                v = f.metadata(k, default=None)
                if v is None:
                    continue
                indices[k].add(v)

        return {k: sorted(list(v)) for k, v in indices.items()}

    def indices(self, squeeze=False):
        r"""Return the unique, sorted values for a set of metadata keys (see below)
        from all the fields. Individual keys can be also queried by :obj:`index`.

        Parameters
        ----------
        squeeze : False
            When True only returns the metadata keys that have more than one values.

        Returns
        -------
        dict
            Unique, sorted metadata values from all the
            :obj:`Field`\ s.

        See Also
        --------
        index

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.indices()
        {'class': ['od'], 'stream': ['oper'], 'levtype': ['pl'], 'type': ['an'],
        'expver': ['0001'], 'date': [20180801], 'time': [1200], 'domain': ['g'],
        'number': [0], 'levelist': [300, 400, 500, 700, 850, 1000],
        'param': ['t', 'u', 'v']}
        >>> ds.indices(squeeze=True)
        {'levelist': [300, 400, 500, 700, 850, 1000], 'param': ['t', 'u', 'v']}
        >>> ds.index("level")
        [300, 400, 500, 700, 850, 1000]

        By default :obj:`indices` uses the keys from the
        "mars" :xref:`eccodes_namespace`. Keys with no valid values are not included. Keys
        that :obj:`index` is called with are automatically added to the original set of keys
        used in :obj:`indices`.

        """
        if not self._md_indices:
            self._md_indices = self._find_all_index_dict()
        if squeeze:
            return {k: v for k, v in self._md_indices.items() if len(v) > 1}
        else:
            return self._md_indices

    def index(self, key):
        r"""Return the unique, sorted values of the specified metadata ``key`` from all the fields.
        ``key`` will be automatically added to the keys returned by :obj:`indices`.

        Parameters
        ----------
        key : str
            Metadata key.

        Returns
        -------
        list
            Unique, sorted values of ``key`` from all the
            :obj:`Field`\ s.

        See Also
        --------
        index

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.index("level")
        [300, 400, 500, 700, 850, 1000]

        """
        if key in self.indices():
            return self.indices()[key]

        self._md_indices[key] = self._find_index_values(key)
        return self._md_indices[key]

    def to_numpy(self, **kwargs):
        r"""Return the field values as an ndarray. It is formed as the array of the
        :obj:`data.core.fieldlist.Field.to_numpy` values per field.

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to :obj:`data.core.fieldlist.Field.to_numpy`

        Returns
        -------
        ndarray
            Array containing the field values.

        See Also
        --------
        values
        """
        import numpy as np

        return np.array([f.to_numpy(**kwargs) for f in self])

    @property
    def values(self):
        r"""ndarray: Get the field values as a 2D ndarray. It is formed as the array of
        :obj:`GribField.values <data.readers.grib.codes.GribField.values>` per field.

        See Also
        --------
        to_numpy


        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> for f in ds:
        ...     print(f.values.shape)
        ...
        (209,)
        (209,)
        >>> v = ds.values
        >>> v.shape
        (2, 209)
        >>> v[0][:3]
        array([262.78027344, 267.44726562, 268.61230469])

        """
        import numpy as np

        return np.array([f.values for f in self])

    def data(self, keys=("lat", "lon", "value"), flatten=False, dtype=None):
        r"""Return the values and/or the geographical coordinates.

        Only works when all the fields have the same grid geometry.

        Parameters
        ----------
        keys: :obj:`str`, :obj:`list` or :obj:`tuple`
            Specifies the type of data to be returned. Any combination of "lat", "lon" and "value"
            is allowed here.
        flatten: bool
            When it is True the "lat", "lon" arrays and the "value" arrays per field
            will all be flattened. Otherwise they will preserve the field's :obj:`shape`.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``np.float64``.

        Returns
        -------
        ndarray
            The elements of the ndarray (in the order of the ``keys``) are as follows:

            * the latitudes array from the first field  when "lat" is in ``keys``
            * the longitudes array from the first field when "lon" is in ``keys``
            * a values array per field when "values" is in ``keys``


        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry.


        Examples
        --------
        - :ref:`/examples/grib_lat_lon_value.ipynb`

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
        >>> len(ds)
        6
        >>> d = ds.data()
        >>> d.shape
        (8, 7, 12)
        >>> d[0, 0, 0]  # first latitude
        90.0
        >>> d[1, 0, 0]  # first longitude
        0.0
        >>> d[2:, 0, 0]  # first value per field
        array([272.56417847,  -6.28688049,   7.83348083, 272.53916931,
                -4.89837646,   8.66096497])
        >>> d = ds.data(keys="lon")
        >>> d.shape
        (1, 7, 12)
        >>> d[0, 0, 0]  # first longitude
        0.0

        See Also
        --------
        to_latlon
        to_points
        to_numpy
        values

        """
        import numpy as np

        if self._is_shared_grid():
            if isinstance(keys, str):
                keys = [keys]

            if "lat" in keys or "lon" in keys:
                latlon = self[0].to_latlon(flatten=flatten, dtype=dtype)

            r = []
            for k in keys:
                if k == "lat":
                    r.append(latlon["lat"])
                elif k == "lon":
                    r.append(latlon["lon"])
                elif k == "value":
                    r.extend([f.to_numpy(flatten=flatten, dtype=dtype) for f in self])
                else:
                    raise ValueError(f"data: invalid argument: {k}")

            return np.array(r)

        elif len(self) == 0:
            return np.array([])
        else:
            raise ValueError("Fields do not have the same grid geometry")

    def metadata(self, *args, **kwargs):
        r"""Return the metadata values for each field.

        Parameters
        ----------
        *args: tuple
            Positional arguments defining the metadata keys. Passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`

        Returns
        -------
        list
            List with one item per :obj:`GribField <data.readers.grib.codes.GribField>`

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.metadata("param")
        ['2t', 'msl']
        >>> ds.metadata("param", "units")
        [('2t', 'K'), ('msl', 'Pa')]
        >>> ds.metadata(["param", "units"])
        [['2t', 'K'], ['msl', 'Pa']]

        """
        result = []
        for s in self:
            result.append(s.metadata(*args, **kwargs))
        return result

    def ls(self, n=None, keys=None, extra_keys=None, namespace=None):
        r"""Generate a list like summary using a set of metadata keys.

        Parameters
        ----------
        n: int, None
            The number of :obj:`Field`\ s to be
            listed. None means all the messages, ``n > 0`` means fields from the front, while
            ``n < 0`` means fields from the back of the fieldlist.
        keys: list of str, dict, None
            Metadata keys. If it is None the following default set of keys will be used:  "centre",
            "shortName", "typeOfLevel", "level", "dataDate", "dataTime", "stepRange", "dataType",
            "number", "gridType". To specify a column title for each key in the output use a dict.
        extra_keys: list of str, dict, None
            List of additional keys to ``keys``. To specify a column title for each key in the output
            use a dict.
        namespace: str, None
            The namespace to choose the ``keys`` from. When it is set ``keys`` and
            ``extra_keys`` are omitted.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row per :obj:`Field`.

        See Also
        --------
        head
        tail

        """
        from earthkit.data.utils.summary import ls

        def _proc(keys, n):
            num = len(self)
            pos = slice(0, num)
            if n is not None:
                pos = slice(0, min(num, n)) if n > 0 else slice(num - min(num, -n), num)
            pos_range = range(pos.start, pos.stop)

            if "namespace" in keys:
                ns = keys.pop("namespace", None)
                for i in pos_range:
                    f = self[i]
                    v = f.metadata(namespace=ns)
                    if len(keys) > 0:
                        v.update(f._attributes(keys))
                    yield (v)
            else:
                for i in pos_range:
                    yield (self[i]._attributes(keys))

        _keys = (
            self._default_ls_keys() if namespace is None else dict(namespace=namespace)
        )
        return ls(_proc, _keys, n=n, keys=keys, extra_keys=extra_keys)

    @cached_method
    def _default_ls_keys(self):
        if len(self) > 0:
            return self[0].metadata().ls_keys()
        else:
            return []

    def head(self, n=5, **kwargs):
        r"""Generate a list like summary of the first ``n``
        :obj:`GribField <data.readers.grib.codes.GribField>`\ s using a set of metadata keys.
        Same as calling :obj:`ls` with ``n``.

        Parameters
        ----------
        n: int, None
            The number of messages (``n`` > 0) to be printed from the front.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See  :obj:`ls`.

        See Also
        --------
        ls
        tail


        The following calls are equivalent:

            .. code-block:: python

                ds.head()
                ds.head(5)
                ds.head(n=5)
                ds.ls(5)
                ds.ls(n=5)

        """
        if n <= 0:
            raise ValueError("head: n must be > 0")
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        r"""Generate a list like summary of the last ``n``
        :obj:`GribField <data.readers.grib.codes.GribField>`\ s using a set of metadata keys.
        Same as calling :obj:`ls` with ``-n``.

        Parameters
        ----------
        n: int, None
            The number of messages (``n`` > 0)  to be printed from the back.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See  :obj:`ls`.

        See Also
        --------
        head
        ls


        The following calls are equivalent:

            .. code-block:: python

                ds.tail()
                ds.tail(5)
                ds.tail(n=5)
                ds.ls(-5)
                ds.ls(n=-5)

        """
        if n <= 0:
            raise ValueError("n must be > 0")
        return self.ls(n=-n, **kwargs)

    def describe(self, *args, **kwargs):
        r"""Generate a summary of the fieldlist."""
        from earthkit.data.utils.summary import format_describe

        def _proc():
            for f in self:
                yield (f._attributes(self._describe_keys()))

        return format_describe(_proc(), *args, **kwargs)

    @cached_method
    def _describe_keys(self):
        if len(self) > 0:
            return self[0].metadata().describe_keys()
        else:
            return []

    def datetime(self):
        r"""Return the unique, sorted list of dates and times in the fieldlist.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".


        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
        >>> ds.datetime()
        {'base_time': [datetime.datetime(2020, 12, 21, 12, 0)],
        'valid_time': [
            datetime.datetime(2020, 12, 21, 12, 0),
            datetime.datetime(2020, 12, 21, 15, 0),
            datetime.datetime(2020, 12, 21, 18, 0),
            datetime.datetime(2020, 12, 21, 21, 0),
            datetime.datetime(2020, 12, 23, 12, 0)]}

        """
        base = set()
        valid = set()
        for s in self:
            d = s.datetime()
            base.add(d["base_time"])
            valid.add(d["valid_time"])
        return {"base_time": sorted(base), "valid_time": sorted(valid)}

    def to_points(self, **kwargs):
        r"""Return the geographical coordinates shared by all the fields in
        the data's original Coordinate Reference System (CRS).

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`Field.to_points() <data.core.fieldlist.Field.to_points>`

        Returns
        -------
        dict
            Dictionary with items "x" and "y", containing the ndarrays of the x and
            y coordinates, respectively.

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry.
        """
        if self._is_shared_grid():
            return self[0].to_points(**kwargs)
        elif len(self) == 0:
            return dict(x=None, y=None)
        else:
            raise ValueError("Fields do not have the same grid geometry")

    def to_latlon(self, **kwargs):
        r"""Return the latitudes/longitudes shared by all the fields.

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to
            :meth:`Field.to_latlon() <data.core.fieldlist.Field.to_latlon>`

        Returns
        -------
        dict
            Dictionary with items "lat" and "lon", containing the ndarrays of the latitudes and
            longitudes, respectively.

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> for f in ds:
        ...     print(f.shape)
        ...
        (11, 19)
        (11, 19)
        >>> r = ds.to_latlon()
        >>> for k, v in r.items():
        ...     print(f"{k}: shape={v.shape}")
        ...
        lat: shape=(11, 19)
        lon: shape=(11, 19)
        >>> r["lon"][:2]
        array([[-27., -23., -19., -15., -11.,  -7.,  -3.,   1.,   5.,   9.,  13.,
         17.,  21.,  25.,  29.,  33.,  37.,  41.,  45.],
        [-27., -23., -19., -15., -11.,  -7.,  -3.,   1.,   5.,   9.,  13.,
         17.,  21.,  25.,  29.,  33.,  37.,  41.,  45.]])

        """
        if self._is_shared_grid():
            return self[0].to_latlon(**kwargs)
        elif len(self) == 0:
            return dict(lat=None, lon=None)
        else:
            raise ValueError("Fields do not have the same grid geometry")

    def projection(self):
        r"""Return the projection information shared by all the fields.

        Returns
        -------
        :obj:`Projection`

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.projection()
        <Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to ...>
        Name: unknown
        Axis Info [cartesian]:
        - E[east]: Easting (unknown)
        - N[north]: Northing (unknown)
        - h[up]: Ellipsoidal height (metre)
        Area of Use:
        - undefined
        Coordinate Operation:
        - name: unknown
        - method: Equidistant Cylindrical
        Datum: Unknown based on WGS 84 ellipsoid
        - Ellipsoid: WGS 84
        - Prime Meridian: Greenwich
        >>> ds.projection().to_proj_string()
        '+proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to_meter=111319.4907932736 +no_defs +type=crs'
        """
        if self._is_shared_grid():
            return self[0].projection()
        elif len(self) == 0:
            return None
        else:
            raise ValueError("Fields do not have the same grid geometry")

    def bounding_box(self):
        r"""Return the bounding box for each field.

        Returns
        -------
        list
            List with one :obj:`BoundingBox <data.utils.bbox.BoundingBox>` per
            :obj:`Field`
        """
        return [s.bounding_box() for s in self]

    @cached_method
    def _is_shared_grid(self):
        if len(self) > 0:
            grid = self[0].metadata().geography._unique_grid_id()
            if grid is not None:
                return all(
                    f.metadata().geography._unique_grid_id() == grid for f in self
                )
        return False

    def save(self, filename, append=False, **kwargs):
        r"""Write all the fields into a file.

        Parameters
        ----------
        filename: str
            The target file path.
        append: bool
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`write`.
        """
        flag = "wb" if not append else "ab"
        with open(filename, flag) as f:
            self.write(f, **kwargs)

    def write(self, f, **kwargs):
        r"""Write all the fields to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        **kwargs: dict, optional
            Other keyword arguments passed to the underlying field implementation.
        """
        for s in self:
            s.write(f, **kwargs)

    def to_fieldlist(self, backend, **kwargs):
        r"""Convert to a new :class:`FieldList` based on the ``backend``.

        When the :class:`FieldList` is already in the required format no new
        :class:`FieldList` is created but the current one is returned.

        Parameters
        ----------
        backend: str
            Specifies the backend for the generated fieldlist. The supported values are as follows:

            - "numpy": the generated fieldlist is a :class:`NumpyFieldList`, which represents
              each field by an ndarray storing the field values and a :class:`MetaData` object holding
              the field metadata. The shape and dtype of the ndarray is controlled by the ``kwargs``.
              Please note that generated :class:`NumpyFieldList` stores all the field values in
              a single ndarray.

        **kwargs: dict, optional
            When ``backend`` is "numpy" ``kwargs`` are passed to :obj:`to_numpy` to
            extract the field values the resulting object will store.

        Returns
        -------
        :class:`FieldList`
            - the current :class:`FieldList` if it is already in the required format
            - :class:`NumpyFieldList` when ``backend`` is "numpy"

        Examples
        --------
        The following example will convert a fieldlist read from a file into a
        :class:`NumpyFieldList` storing single precision field values.

        >>> import numpy as np
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.path
        'docs/examples/tuv_pl.grib'
        >>> r = ds.to_fieldlist("numpy", dtype=np.float32)
        >>> r
        NumpyFieldList(fields=18)
        >>> hasattr(r, "path")
        False
        >>> r.to_numpy().dtype
        dtype('float32')

        """
        converter = fieldlist_converters.get(backend, None)
        if converter is not None:
            return getattr(self, converter)(**kwargs)

    def _to_numpy_fieldlist(self, **kwargs):
        md = [f.metadata() for f in self]
        return self.from_numpy(self.to_numpy(**kwargs), md)


fieldlist_converters = {"numpy": "_to_numpy_fieldlist"}
