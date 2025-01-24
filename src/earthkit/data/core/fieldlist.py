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
from functools import cached_property

import deprecation

from earthkit.data.core import Base
from earthkit.data.core.index import Index
from earthkit.data.core.index import MaskIndex
from earthkit.data.core.index import MultiIndex
from earthkit.data.decorators import cached_method
from earthkit.data.decorators import detect_out_filename
from earthkit.data.utils.array import array_namespace
from earthkit.data.utils.array import array_to_numpy
from earthkit.data.utils.array import convert_array
from earthkit.data.utils.array import get_backend
from earthkit.data.utils.metadata.args import metadata_argument


class FieldListIndices:
    def __init__(self, field_list):
        self.fs = field_list
        self.user_indices = dict()

    @cached_property
    def default_index_keys(self):
        if len(self.fs) > 0:
            return self.fs[0]._metadata.index_keys()
        else:
            return []

    def _index_value(self, key):
        values = set()
        for f in self.fs:
            v = f.metadata(key, default=None)
            if v is not None:
                values.add(v)

        return sorted(list(values))

    @cached_property
    def default_indices(self):
        indices = defaultdict(set)
        keys = self.default_index_keys
        for f in self.fs:
            v = f.metadata(keys, default=None)
            for i, k in enumerate(keys):
                if v[i] is not None:
                    indices[k].add(v[i])

        return {k: sorted(list(v)) for k, v in indices.items()}

    def indices(self, squeeze=False):
        r = {**self.default_indices, **self.user_indices}

        if squeeze:
            return {k: v for k, v in r.items() if len(v) > 1}
        else:
            return r

    def index(self, key):
        if key in self.user_indices:
            return self.user_indices[key]

        if key in self.default_index_keys:
            return self.default_indices[key]

        self.user_indices[key] = self._index_value(key)
        return self.user_indices[key]


class Field(Base):
    r"""Represent a Field."""

    @property
    def array_backend(self):
        r""":obj:`ArrayBackend`: Return the array backend of the field."""
        return get_backend(self._values())

    @abstractmethod
    def _values(self, dtype=None):
        r"""Return the raw values extracted from the underlying storage format
        of the field.

        Parameters
        ----------
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.

        The original shape and array type of the raw values are kept.

        Returns
        -------
        array-like
            Field values.

        """
        self._not_implemented()

    @property
    def values(self):
        r"""array-like: Get the values stored in the field as a 1D array."""
        return self._flatten(self._values())

    @property
    @abstractmethod
    def _metadata(self):
        r"""Metadata: Get the object representing the field's metadata."""
        self._not_implemented()

    def to_numpy(self, flatten=False, dtype=None, index=None):
        r"""Return the values stored in the field as an ndarray.

        Parameters
        ----------
        flatten: bool
            When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        index: ndarray indexing object, optional
            The index of the values and to be extracted. When it
            is None all the values are extracted

        Returns
        -------
        ndarray
            Field values

        """
        v = array_to_numpy(self._values(dtype=dtype))
        shape = self._required_shape(flatten)
        if shape != v.shape:
            v = v.reshape(shape)
        if index is not None:
            v = v[index]
        return v

    def to_array(self, flatten=False, dtype=None, array_backend=None, index=None):
        r"""Return the values stored in the field.

        Parameters
        ----------
        flatten: bool
            When it is True a flat array is returned. Otherwise an array with the field's
            :obj:`shape` is returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        array_backend: str, module or None
            The array backend to be used. When it is :obj:`None` the underlying array format
            of the field is used.
        index: array indexing object, optional
            The index of the values and to be extracted. When it
            is None all the values are extracted

        Returns
        -------
        array-array
            Field values.

        """
        v = self._values(dtype=dtype)
        if array_backend is not None:
            v = convert_array(v, target_backend=array_backend)

        v = self._reshape(v, flatten)
        if index is not None:
            v = v[index]
        return v

    def data(self, keys=("lat", "lon", "value"), flatten=False, dtype=None, index=None):
        r"""Return the values and/or the geographical coordinates for each grid point.

        Parameters
        ----------
        keys: :obj:`str`, :obj:`list` or :obj:`tuple`
            Specifies the type of data to be returned. Any combination of "lat", "lon" and "value"
            is allowed here.
        flatten: bool
            When it is True a flat array per key is returned. Otherwise an array with the field's
            :obj:`shape` is returned for each key.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        index: array indexing object, optional
            The index of the values and or the latitudes/longitudes to be extracted. When it
            is None all the values and/or coordinates are extracted.

        Returns
        -------
        array-like
            An multi-dimensional array containing one array per key is returned
            (following the order in ``keys``). The underlying array format
            of the field is used. When ``keys`` is a single value only the
            array belonging to the key is returned.

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

        r = {}
        for k in keys:
            # TODO: convert dtype
            v = _keys[k](dtype=dtype)
            v = self._reshape(v, flatten)
            if index is not None:
                v = v[index]
            r[k] = v

        # convert latlon to array format
        ll = {k: r[k] for k in r if k != "value"}
        if ll:
            sample = r.get("value", None)
            if sample is None:
                sample = self._values(dtype=dtype)
            for k, v in zip(ll.keys(), convert_array(list(ll.values()), target_array_sample=sample)):
                r[k] = v

        r = list(r.values())
        if len(r) == 1:
            return r[0]
        else:
            return array_namespace(r[0]).stack(r)

    def to_points(self, flatten=False, dtype=None, index=None):
        r"""Return the geographical coordinates in the data's original
        Coordinate Reference System (CRS).

        Parameters
        ----------
        flatten: bool
            When it is True 1D arrays are returned. Otherwise arrays with the field's
            :obj:`shape` are returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.
        index: array indexing object, optional
            The index of the coordinates to be extracted. When it is None
            all the values are extracted.

        Returns
        -------
        dict
            Dictionary with items "x" and "y", containing the arrays of the x and
            y coordinates, respectively. The underlying array format
            of the field is used.

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
        r = {}
        if x is not None and y is not None:
            x = self._reshape(x, flatten)
            y = self._reshape(y, flatten)
            if index is not None:
                x = x[index]
                y = y[index]
            r = dict(x=x, y=y)
        elif self.projection().CARTOPY_CRS == "PlateCarree":
            lon, lat = self.data(("lon", "lat"), flatten=flatten, dtype=dtype, index=index)
            return dict(x=lon, y=lat)
        else:
            raise ValueError("to_points(): geographical coordinates in original CRS are not available")

        # convert values to array format
        assert r
        sample = self._values(dtype=dtype)
        for k, v in zip(r.keys(), convert_array(list(r.values()), target_array_sample=sample)):
            r[k] = v
        return r

    def to_latlon(self, flatten=False, dtype=None, index=None):
        r"""Return the latitudes/longitudes of all the gridpoints in the field.

        Parameters
        ----------
        flatten: bool
            When it is True 1D arrays are returned. Otherwise arrays with the field's
            :obj:`shape` are returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.
        index: array indexing object, optional
            The index of the latitudes/longitudes to be extracted. When it is None
            all the values are extracted.

        Returns
        -------
        dict
            Dictionary with items "lat" and "lon", containing the arrays of the latitudes and
            longitudes, respectively. The underlying array format
            of the field is used.

        See Also
        --------
        to_points

        """
        lon, lat = self.data(("lon", "lat"), flatten=flatten, dtype=dtype, index=index)
        return dict(lat=lat, lon=lon)

    def grid_points(self):
        r = self.to_latlon(flatten=True)
        return r["lat"], r["lon"]

    def grid_points_unrotated(self):
        lat = self._metadata.geography.latitudes_unrotated()
        lon = self._metadata.geography.longitudes_unrotated()
        return lat, lon

    @property
    def rotation(self):
        return self._metadata.geography.rotation

    @property
    def resolution(self):
        return self._metadata.geography.resolution()

    @property
    def mars_grid(self):
        return self._metadata.geography.mars_grid()

    @property
    def mars_area(self):
        return self._metadata.geography.mars_area()

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

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
        >>> ds[4].datetime()
        {'base_time': datetime.datetime(2020, 12, 21, 12, 0),
        'valid_time': datetime.datetime(2020, 12, 21, 18, 0)}

        """
        return self._metadata.datetime()

    def valid_datetime(self):
        self._not_implemented()

    def base_datetime(self):
        self._not_implemented()

    def h_datetime(self):
        self._not_implemented()

    def an_datetime(self):
        self._not_implemented()

    def indexing_datetime(self):
        self._not_implemented()

    def metadata(self, *keys, astype=None, remapping=None, patches=None, **kwargs):
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
        remapping: dict, optional
            Creates new metadata keys from existing ones that we can refer to in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{param}{level}"}
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

        if remapping is not None or patches is not None:
            from earthkit.data.core.order import build_remapping

            remapping = build_remapping(remapping, patches)
            return remapping(self.metadata)(*keys, astype=astype, **kwargs)

        # when called without arguments returns the metadata object
        if len(keys) == 0 and astype is None and not kwargs:
            return self._metadata

        namespace = kwargs.pop("namespace", None)
        key, namespace, astype, key_arg_type = metadata_argument(*keys, namespace=namespace, astype=astype)

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

            if key_arg_type is str:
                return r[0]
            elif key_arg_type is tuple:
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

    @deprecation.deprecated(deprecated_in="0.13.0", details="Use to_target() instead")
    def save(self, filename, append=False, **kwargs):
        r"""Write the field into a file.

        Parameters
        ----------
        filename: str, optional
            The target file path, if not defined attempts will be made to detect the filename
        append: bool, optional
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists. Default is False
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`write`.
        """
        self.to_target("file", filename, append=append, **kwargs)
        # the original implementation
        # flag = "wb" if not append else "ab"
        # with open(filename, flag) as f:
        #     self.write(f, **kwargs)

    @deprecation.deprecated(deprecated_in="0.13.0", details="Use to_target() instead")
    def write(self, f, **kwargs):
        self.to_target("file", f, **kwargs)

    def _write(self, target, **kwargs):
        assert target is not None
        target._write(self, **kwargs)

    def to_target(self, target, *args, **kwargs):
        r"""Write the field into a target object.

        Parameters
        ----------
        target: object
            The target object to write the field into.
        *args: tuple
            Positional arguments used to specify the target object.
        **kwargs: dict, optional
            Other keyword arguments used to write the field into the target object.
        """
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def default_encoder(self):
        return self._metadata.data_format()

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        return encoder._encode_field(self, **kwargs)

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

    def _attributes(self, names, remapping=None, joiner=None, default=None):
        result = {}
        metadata = self._metadata.get
        if remapping is not None:
            metadata = remapping(metadata, joiner=joiner)

        for name in names:
            result[name] = metadata(name, default=default)
        return result

        # return {name: metadata(name) for name in names}

    @abstractmethod
    def clone(self, *, values=None, metadata=None, **kwargs):
        r"""Create a new :class:`ClonedField` the with updated values and/or metadata.

        Parameters
        ----------
        values: array-like or None
            The values to be stored in the new :class:`ClonedField`. When it is ``None`` the resulting
            :class:`ClonedField` will access the values from the original field.
        metadata: dict, :class:`Metadata` or None
            If it is a dictionary, it is merged with ``**kwargs`` and interpreted in the same way
            as ``**kwargs``. If it is a :class:`Metadata` object, it is used as the new metadata. In
            this case ``**kwargs`` cannot be used.
        **kwargs: dict, optional
            Keys and values to update the metadata with. Metadata values can also be ``callables``
            with the following positional arguments: original_field, key, original_metadata.
            The new :class:`ClonedField` will contain a reference to the original metadata object and
            keys not present in ``kwargs`` will be accessed from the original field.

        Returns
        -------
        :class:`ClonedField`
            The new field with updated values and/or metadata keeping a
            reference to the original field.

        Raises
        ------
        ValueError
            If ``metadata`` is a :class:`Metadata` object and ``**kwargs`` is not empty.

        """
        self.not_implemented()

    def copy(self, *, values=None, flatten=False, dtype=None, array_backend=None, metadata=None):
        r"""Create a new :class:`ArrayField` by copying the values and metadata.

        Parameters
        ----------
        values: array-like or None
            The values to be stored in the new :class:`Field`. When it is ``None`` the values
            extracted from the original field by using :obj:`to_array` with ``flatten``, ``dtype``
            and ``array_backend`` and copied to the new field.
        flatten: bool
            Control the shape of the values when they are extracted from the original field.
            When ``True``, flatten the array, otherwise the field's shape is kept. Only used when
            ``values`` is not provided.
        dtype: str, array.dtype or None
            Control the typecode or data-type of the values when they are extracted from
            the original field. If :obj:`None`, the default type used by the underlying
            data accessor is used. For GRIB it is ``float64``. Only used when  ``values``
            is not provided.
        array_backend: str, module or None
            Control the array backend of the values when they are extracted from
            the original field. If :obj:`None`, the underlying array format
            of the field is used. Only used when ``values`` is not provided.
        metadata: :class:`Metadata` or None
            The metadata to be stored in the new :class:`Field`. When it is :obj:`None`
            a copy of the metadata of the original field is used.

        Returns
        -------
        :class:`ArrayField`
        """
        from earthkit.data.sources.array_list import ArrayField

        if values is None:
            values = self.to_array(
                flatten=flatten,
                dtype=dtype,
                array_backend=array_backend,
            )

        if metadata is None:
            metadata = self._metadata.override()

        return ArrayField(
            values,
            metadata,
        )

    def to_xarray(self, *args, **kwargs):
        """Convert the Field into an Xarray Dataset.

        Parameters
        ----------
        *args: tuple
            Positional arguments passed to :obj:`FieldList.to_xarray`.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`FieldList.to_xarray`.

        Returns
        -------
        Xarray Dataset

        """
        return self._to_fieldlist().to_xarray(*args, **kwargs)

    def ls(self, *args, **kwargs):
        r"""Generate a list like summary using a set of metadata keys.

        Parameters
        ----------
        *args: tuple
            Positional arguments passed to :obj:`FieldList.ls`.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`FieldList.ls`.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row.

        """
        return self._to_fieldlist().ls(*args, **kwargs)

    def describe(self, *args, **kwargs):
        r"""Generate a summary of the Field."""
        return self._to_fieldlist().describe(*args, **kwargs)

    def _to_fieldlist(self):
        return FieldList.from_fields([self])

    @staticmethod
    def _flatten(v):
        """Flatten the array without copying the data."

        Parameters
        ----------
        v: array-like
            The array to be flattened.

        Returns
        -------
        array-like
            1-D array.
        """
        if len(v.shape) != 1:
            n = math.prod(v.shape)
            n = (n,)
            return array_namespace(v).reshape(v, n)
        return v

    def _reshape(self, v, flatten):
        """Reshape the array to the required shape."""
        shape = self._required_shape(flatten)
        if shape != v.shape:
            v = array_namespace(v).reshape(v, shape)
        return v

    def _required_shape(self, flatten, shape=None):
        """Return the required shape of the array."""
        if shape is None:
            shape = self.shape
        return shape if not flatten else (math.prod(shape),)

    def _array_matches(self, array, flatten=False, dtype=None):
        """Check if the array matches the field and conditions."""
        shape = self._required_shape(flatten)
        return shape == array.shape and (dtype is None or dtype == array.dtype)


class FieldList(Index):
    r"""Represent a list of :obj:`Field` \s."""

    def __init__(self, **kwargs):
        if "array_backend" in kwargs:
            import warnings

            warnings.warn(
                (
                    "array_backend option is not supported any longer in FieldList!"
                    " Use to_fieldlist() instead"
                ),
                DeprecationWarning,
            )
            kwargs.pop("array_backend", None)

        super().__init__(**kwargs)

    def _init_from_mask(self, index):
        pass

    def _init_from_multi(self, index):
        pass

    @staticmethod
    def from_fields(fields):
        r"""Create a :class:`SimpleFieldList`.

        Parameters
        ----------
        fields: iterable
            Iterable of :obj:`Field` objects.

        Returns
        -------
        :class:`SimpleFieldList`

        """
        from earthkit.data.indexing.fieldlist import SimpleFieldList

        return SimpleFieldList([f for f in fields])

    @staticmethod
    def from_numpy(array, metadata):
        return FieldList.from_array(array, metadata)

    @staticmethod
    def from_array(array, metadata):
        r"""Create an :class:`SimpleFieldList`.

        Parameters
        ----------
        array: array-like, list
            The fields' values. When it is a list it must contain one array per field.
        metadata: list, :class:`Metadata`
            The fields' metadata. Must contain one :class:`Metadata` object per field. Or
            it can be a single :class:`Metadata` object when all the fields have the same metadata.

        In the generated :class:`SimpleFieldList`, each field is represented by an array
        storing the field values and a :class:`MetaData` object holding
        the field metadata. The shape and dtype of the array is controlled by the ``kwargs``.
        """
        from earthkit.data.sources.array_list import from_array

        return from_array(array, metadata)

    def ignore(self):
        # When the concrete type is Fieldlist we assume the object was
        # created with Fieldlist() i.e. it is empty. We ignore it from
        # all the merge operations.
        if type(self) is FieldList:
            return True
        else:
            return False

    @cached_property
    def _md_indices(self):
        return FieldListIndices(self)

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
        return self._md_indices.indices(squeeze=squeeze)

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
        return self._md_indices.index(key)

    def _as_array(self, accessor, **kwargs):
        """Use pre-allocated target array to store the field values."""

        def _vals(f):
            return getattr(f, accessor)(**kwargs) if not is_property else getattr(f, accessor)

        n = len(self)
        if n > 0:
            it = iter(self)
            first = next(it)
            is_property = not callable(getattr(first, accessor, None))
            vals = _vals(first)
            ns = array_namespace(vals)
            shape = (n, *vals.shape)
            r = ns.empty(shape, dtype=vals.dtype)
            r[0] = vals
            for i, f in enumerate(it, start=1):
                r[i] = _vals(f)
            return r

    def to_numpy(self, **kwargs):
        r"""Return all the fields' values as an ndarray. It is formed as the array of the
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
        to_array
        values
        """
        return self._as_array("to_numpy", **kwargs)

    def to_array(self, **kwargs):
        r"""Return all the fields' values as an array. It is formed as the array of the
        :obj:`data.core.fieldlist.Field.to_array` values per field.

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to :obj:`data.core.fieldlist.Field.to_array`

        Returns
        -------
        array-like
            Array containing the field values.

        See Also
        --------
        values
        to_numpy
        """
        return self._as_array("to_array", **kwargs)

    @property
    def values(self):
        r"""array-like: Get all the fields' values as a 2D array. It is formed as the array of
        :obj:`GribField.values <data.readers.grib.codes.GribField.values>` per field.

        See Also
        --------
        to_array

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
        return self._as_array("values")

    def data(
        self,
        keys=("lat", "lon", "value"),
        flatten=False,
        dtype=None,
        index=None,
    ):
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
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.
        index: array indexing object, optional
            The index of the values to be extracted from each field. When it is None all the
            values are extracted.

        Returns
        -------
        array-like
            The elements of the array (in the order of the ``keys``) are as follows:

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
        if self._is_shared_grid():
            if isinstance(keys, str):
                keys = [keys]

            if "lat" in keys or "lon" in keys:
                latlon = self[0].to_latlon(flatten=flatten, dtype=dtype, index=index)

            r = []
            for k in keys:
                if k == "lat":
                    r.append(latlon["lat"])
                elif k == "lon":
                    r.append(latlon["lon"])
                elif k == "value":
                    r.extend([f.to_array(flatten=flatten, dtype=dtype, index=index) for f in self])
                else:
                    raise ValueError(f"data: invalid argument: {k}")
            return array_namespace(r[0]).stack(r)

        elif len(self) == 0:
            return array_namespace(r[0]).array_ns.stack([])
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

        _keys = self._default_ls_keys() if namespace is None else dict(namespace=namespace)
        return ls(_proc, _keys, n=n, keys=keys, extra_keys=extra_keys)

    @cached_method
    def _default_ls_keys(self):
        if len(self) > 0:
            return self[0]._metadata.ls_keys()
        else:
            return []

    def head(self, n=5, **kwargs):
        r"""Generate a list like summary of the first ``n`` :obj:`Field`\ s.
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

        Notes
        -----
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
        r"""Generate a list like summary of the last ``n`` :obj:`Field`\ s.
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

        Notes
        -----
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
            return self[0]._metadata.describe_keys()
        else:
            return []

    def datetime(self):
        r"""Return the unique, sorted list of dates and times in the fieldlist.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".

        Examples
        --------
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
            Dictionary with items "x" and "y", containing the arrays of the x and
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

    def to_latlon(self, index=None, **kwargs):
        r"""Return the latitudes/longitudes shared by all the fields.

        Parameters
        ----------
        index: array indexing object, optional
            The index of the latitudes/longitudes to be extracted. When it is None
            all the values are extracted.
        **kwargs: dict, optional
            Keyword arguments passed to
            :meth:`Field.to_latlon() <data.core.fieldlist.Field.to_latlon>`

        Returns
        -------
        dict
            Dictionary with items "lat" and "lon", containing the arrays of the latitudes and
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
            grid = self[0]._metadata.geography._unique_grid_id()
            if grid is not None:
                return all(f._metadata.geography._unique_grid_id() == grid for f in self)
        return False

    @deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use to_target() instead")
    @detect_out_filename
    def save(self, filename, append=False, **kwargs):
        r"""Write all the fields into a file.

        Parameters
        ----------
        filename: str, optional
            The target file path, if not defined attempts will be made to detect the filename
        append: bool, optional
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists. Default is False
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`write`.

        See Also
        --------
        :obj:`write`
        :meth:`GribFieldList.save() <data.readers.grib.index.GribFieldList.save>`
        :meth:`SimpleFieldList.save() <data.indexing.fieldlist.SimpleFieldList.save>`

        """
        metadata = {}
        bits_per_value = kwargs.pop("bits_per_value", None)
        if bits_per_value is not None:
            metadata = {"bitsPerValue": bits_per_value}

        self.to_target("file", filename, append=append, metadata=metadata, **kwargs)

        # original code
        # flag = "wb" if not append else "ab"
        # with open(filename, flag) as f:
        #     self.write(f, **kwargs)

    @deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use to_target() instead")
    def write(self, f, **kwargs):
        r"""Write all the fields to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        **kwargs: dict, optional
            Other keyword arguments passed to the underlying field implementation.

        See Also
        --------
        read

        """

        metadata = {}
        bits_per_value = kwargs.pop("bits_per_value", None)
        if bits_per_value is not None:
            metadata = {"bitsPerValue": bits_per_value}

        self.to_target("file", f, metadata=metadata, **kwargs)

        # original code
        # for s in self:
        #     s.write(f, **kwargs)

    def _write(self, target, **kwargs):
        assert target is not None
        target._write(self, **kwargs)

    def default_encoder(self):
        if len(self) > 0:
            return self[0]._metadata.data_format()

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        return encoder._encode_fieldlist(self, **kwargs)

    def to_tensor(self, *args, **kwargs):
        from earthkit.data.indexing.tensor import FieldListTensor

        return FieldListTensor.from_fieldlist(self, *args, **kwargs)

    def to_fieldlist(self, array_backend=None, **kwargs):
        r"""Convert to a new :class:`FieldList`.

        Parameters
        ----------
        array_backend: str, module, :obj:`ArrayBackend`
            Specifies the array backend for the generated :class:`FieldList`. The array
            type must be supported by :class:`ArrayBackend`.

        **kwargs: dict, optional
            ``kwargs`` are passed to :obj:`to_array` to
            extract the field values the resulting object will store.

        Returns
        -------
        :class:`SimpleFieldList`
            - a new fieldlist containing :class`ArrayField` fields

        Examples
        --------
        The following example will convert a fieldlist read from a file into a
        :class:`SimpleFieldList` storing single precision field values.

        >>> import numpy as np
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.path
        'docs/examples/tuv_pl.grib'
        >>> r = ds.to_fieldlist(array_backend="numpy", dtype=np.float32)
        >>> r
        SimpleFieldList(fields=18)
        >>> hasattr(r, "path")
        False
        >>> r.to_numpy().dtype
        dtype('float32')

        """
        return self.from_fields([f.copy(array_backend=array_backend, **kwargs) for f in self])

    def cube(self, *args, **kwargs):
        from earthkit.data.indexing.cube import FieldCube

        return FieldCube(self, *args, **kwargs)

    @classmethod
    def new_mask_index(self, *args, **kwargs):
        return MaskFieldList(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, FieldList) for _ in sources)
        return MultiFieldList(sources)

    def _cache_diag(self):
        """For testing only"""
        from earthkit.data.utils.diag import metadata_cache_diag

        return metadata_cache_diag(self)


class MaskFieldList(FieldList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class MultiFieldList(FieldList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
