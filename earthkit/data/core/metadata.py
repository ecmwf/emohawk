# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta, abstractmethod

from earthkit.data.core.constants import DATETIME, GRIDSPEC


class Metadata(metaclass=ABCMeta):
    r"""Base class to represent metadata.

    Metadata is a dict-like immutable object. Modification is possible
    with :obj:`override`, which always creates a new object.

    Implemented in subclasses: :obj:`RawMetadata`, :obj:`GribMetadata`.

    Examples
    --------
    - :ref:`/examples/metadata.ipynb`

    """

    def __iter__(self):
        """Return an iterator over the metadata keys."""
        return iter(self.keys())

    @abstractmethod
    def __len__(self):
        r"""Return the number of metadata entries."""

    def __getitem__(self, key):
        r"""Return the value for ``key``.

        Raises
        ------
        KeyError
            When ``key`` is not available.
        """
        return self._get_key(key)

    @abstractmethod
    def __contains__(self, key):
        r"""Check if ``key`` is available.

        Returns
        -------
        bool
        """
        pass

    @abstractmethod
    def keys(self):
        r"""Return a new view of the metadata keys.

        Returns
        -------
        Iterable of str

        """
        pass

    @abstractmethod
    def items(self):
        r"""Return a new view of the metadata items.

        Returns
        -------
        Iterable of :obj:`(key,value)` pairs

        """
        pass

    def get(self, key, default=None):
        r"""Return the value for ``key``.

        Parameters
        ----------
        key: str
            Metadata key
        default:
            When ``key`` is not found ``default`` is returned.
        """
        return self._get_key(key, default=default, raise_on_missing=False)

    def _get_key(self, key, astype=None, default=None, raise_on_missing=True):
        r"""Return the value for ``key``.

        Parameters
        ----------
        key: str
            Metadata key
        default: value
            Specify the default value for ``key``. Returned when ``key``
            is not found or its value is a missing value and raise_on_missing is ``False``.
        raise_on_missing: bool
            When it is True raises an exception if ``key`` is not found or
            it has a missing value.

        Returns
        -------
        value
            Returns the ``key`` value. Returns ``default`` if ``key`` is not found
            or it has a missing value and ``raise_on_missing`` is False.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and ``key`` is not found or it has
            a missing value.

        """
        # check for custom keys
        is_custom, v = self._get_custom_key(
            key, default=default, raise_on_missing=raise_on_missing
        )
        if is_custom:
            return v

        return self._get_internal_key(
            key, astype=astype, default=default, raise_on_missing=raise_on_missing
        )

    @abstractmethod
    def _get_internal_key(self, key, astype=None, default=None, raise_on_missing=True):
        pass

    def _get_custom_key(self, key, default=None, raise_on_missing=True):
        try:
            if key == DATETIME:
                return True, self.datetime().get("valid_time")
            elif key == GRIDSPEC:
                return True, self.grid_spec
        except Exception as e:
            if not raise_on_missing:
                return default
            else:
                raise KeyError(f"{key}, reason={e}")
        return False, None

    @abstractmethod
    def override(self, *args, **kwargs):
        r"""Change the metadata values and return a new object.

        :obj:`override` accepts another :obj:`Metadata` or a dict or
        an iterable of key/value pairs (as tuples or other iterables of length two).
        If keyword arguments are specified, the metadata is then updated with those
        key/value pairs.

        Examples
        --------
        >>> other = RawMetadata({"key1": 1, "key2": 2})
        >>> m1 = m.override(other)
        >>> m1 = m.override({"key1": 1, "key2": 2})
        >>> m1 = m.override([("key1", 1), ("key2", 2)])
        >>> m1 = m.override(key1=1, key2=2)
        """
        pass

    def namespaces(self):
        r"""Return the available namespaces.

        Returns
        -------
        list of str
        """
        return []

    def as_namespace(self, namespace=None):
        r"""Return all the keys/values from a namespace.

        Parameters
        ----------
        namespace: str, None
            The namespace. When `namespace` is None or an empty :obj:`str` all the available
            keys/values are returned.

        Returns
        -------
        dict
            All the keys/values from the `namespace`.

        """
        if namespace is None or namespace == "":
            return {k: v for k, v in self.items()}
        return {}

    def dump(self, **kwargs):
        r"""Generate a dump from the metadata content."""
        return None

    def datetime(self):
        r"""Return the date and time.

        Returns
        -------
        dict of datatime.datetime or None
            Dict with items "base_time" and "valid_time". None if
            date and time are not available.
        """
        return None

    @property
    def geography(self):
        r""":obj:`Geography`: Get geography description.

        If it is not available None is returned.
        """
        return None

    @property
    def gridspec(self):
        r""":ref:`~data.core.gridspec.GridSpec`: Get grid description.

        If it is not available None is returned.
        """
        return None if self.geography is None else self.geography.gridspec()

    def ls_keys(self):
        r"""Return the keys to be used with the :meth:`ls` method."""
        return []

    def describe_keys(self):
        r"""Return the keys to be used with the :meth:`describe` method."""
        return []

    def index_keys(self):
        r"""Return the keys to be used with the :meth:`indices` method."""
        return []


class RawMetadata(Metadata):
    r"""Metadata implementation based on key/value pairs.

    >>> from earthkit.data.core.metadata import RawMetadata
    >>> md = RawMetadata({"shortName": "2t", "perturbationNumber": 5})
    >>> md = RawMetadata([("shortName", "2t"), ("perturbationNumber", 5)])
    >>> md = RawMetadata(shortName="2t", perturbationNumber=5)
    >>> md
    RawMetadata({'shortName': '2t', 'perturbationNumber': 5})
    >>> md2 = RawMetadata(md)
    >>> md2
    RawMetadata({'shortName': '2t', 'perturbationNumber': 5})

    Value access:

    >>> "shortName" in md
    True
    >>> md["shortName"]
    '2t'
    >>> md.get("shortName")
    '2t'
    >>> "step" in md
    False
    >>> md.get("step")
    >>> md.get("step", 0)
    0

    Examples
    --------
    - :ref:`/examples/metadata.ipynb`

    """

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)

    def __len__(self):
        return len(self._d)

    def keys(self):
        return self._d.keys()

    def items(self):
        return self._d.items()

    def __contains__(self, key):
        return key in self._d

    def _get_internal_key(self, key, astype=None, default=None, raise_on_missing=True):
        if not raise_on_missing:
            v = self._d.get(key, default)
        else:
            v = self._d[key]

        if astype is not None:
            try:
                return astype(v)
            except Exception:
                return None
        return v

    def override(self, *args, **kwargs):
        d = dict(**self._d)
        d.update(*args, **kwargs)
        return RawMetadata(d)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._d.__repr__()})"
