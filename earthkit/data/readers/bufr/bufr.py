# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
from abc import abstractmethod

import eccodes
from pdbufr.high_level_bufr.bufr import bufr_code_is_coord

from earthkit.data.core import Base
from earthkit.data.core.index import Index, MaskIndex, MultiIndex
from earthkit.data.utils.message import (
    CodesHandle,
    CodesMessagePositionIndex,
    CodesReader,
)
from earthkit.data.utils.metadata import metadata_argument
from earthkit.data.utils.parts import Part
from earthkit.data.utils.summary import make_bufr_html_tree

from .. import Reader
from .pandas import PandasMixIn

BUFR_LS_KEYS = {
    "edition": "edition",
    "type": "dataCategory",
    "subtype": "dataSubCategory",
    "c": "bufrHeaderCentre",
    "mv": "masterTablesVersionNumber",
    "lv": "localTablesVersionNumber",
    "subsets": "numberOfSubsets",
    "compr": "compressedData",
    "typicalDate": "typicalDate",
    "typicalTime": "typicalTime",
    "ident": "ident",
    "lat": "localLatitude",
    "lon": "localLongitude",
}


class BufrCodesMessagePositionIndex(CodesMessagePositionIndex):
    # This does not belong here, should be in the C library
    def _get_message_positions(self, path):
        fd = os.open(path, os.O_RDONLY)
        try:

            def get(count):
                buf = os.read(fd, count)
                assert len(buf) == count
                return int.from_bytes(
                    buf,
                    byteorder="big",
                    signed=False,
                )

            offset = 0
            while True:
                code = os.read(fd, 4)
                if len(code) < 4:
                    break

                if code != b"BUFR":
                    offset = os.lseek(fd, offset + 1, os.SEEK_SET)
                    continue

                length = get(3)
                edition = get(1)

                if edition in [3, 4]:
                    yield offset, length
                    offset = os.lseek(fd, offset + length, os.SEEK_SET)

        finally:
            os.close(fd)


class BUFRCodesHandle(CodesHandle):
    PRODUCT_ID = eccodes.CODES_PRODUCT_BUFR

    def __init__(self, handle, path, offset):
        super().__init__(handle, path, offset)
        self._unpacked = False

    def unpack(self):
        """Decode data section"""
        if not self._unpacked:
            eccodes.codes_set(self._handle, "unpack", 1)
            self._unpacked = True

    def pack(self):
        """Encode data section"""
        if self._unpacked:
            eccodes.codes_set(self._handle, "pack", 1)
            self._unpacked = False

    def json_dump(self, path):
        self.unpack()
        with open(path, "w") as f:
            eccodes.codes_dump(self._handle, f, "json")
        self.pack()

    def __iter__(self):
        class _KeyIterator:
            def __init__(self, handle):
                self._iterator = eccodes.codes_bufr_keys_iterator_new(handle)

            def __del__(self):
                try:
                    eccodes.codes_bufr_keys_iterator_delete(self._iterator)
                except Exception:
                    pass

            def __iter__(self):
                return self

            def __next__(self):
                while True:
                    if not eccodes.codes_bufr_keys_iterator_next(self._iterator):
                        raise StopIteration

                    return eccodes.codes_bufr_keys_iterator_get_name(self._iterator)

        return _KeyIterator(self._handle)

    def keys(self, namespace=None):
        """Iterate over all the available keys"""
        return self.__iter__()

    def as_namespace(self, namespace=None):
        return {k: self.get(k) for k in self.keys(namespace=namespace)}


class BUFRCodesReader(CodesReader):
    PRODUCT_ID = eccodes.CODES_PRODUCT_BUFR
    HANDLE_TYPE = BUFRCodesHandle


class BUFRMessage(Base):
    r"""Represents a BUFR message in a BUFR file.

    Parameters
    ----------
    path: str
        Path to the BUFR file
    offset: number
        File offset of the message (in bytes)
    length: number
        Size of the message (in bytes)
    """

    def __init__(self, path, offset, length):
        self.path = path
        self._offset = offset
        self._length = length
        self._handle = None

    @property
    def handle(self):
        r""":class:`CodesHandle`: Gets an object providing access to the low level BUFR message structure."""
        if self._handle is None:
            assert self._offset is not None
            self._handle = BUFRCodesReader.from_cache(self.path).at_offset(self._offset)
        return self._handle

    def __repr__(self):
        return "BUFRMessage(type=%s,subType=%s,subsets=%s,%s,%s)" % (
            self.handle.get("dataCategory", default=None),
            self.handle.get("dataSubCategory", default=None),
            self.handle.get("numberOfSubsets", default=None),
            self.handle.get("typicalDate", default=None),
            self.handle.get("typicalTime", default=None),
        )

    def _header(self, key):
        return self.handle.get(key, default=None)

    def subset_count(self):
        """Returns the number of subsets in the given BUFR message."""
        return self._header("numberOfSubsets")

    def is_compressed(self):
        """Checks if the BUFR message contains compressed subsets."""
        return self.subset_count() > 1 and self._header("compressedData") == 1

    def is_uncompressed(self):
        """Checks if the BUFR message contains uncompressed subsets."""
        return self.subset_count() > 1 and self._header("compressedData") == 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handle = None

    def __setitem__(self, key, value):
        """Sets value associated with ``key``"""
        if isinstance(value, list):
            return eccodes.codes_set_array(self.handle._handle, key, value)
        else:
            return eccodes.codes_set(self.handle._handle, key, value)

    def __getitem__(self, key):
        """Returns the value of the ``key``."""
        return self.handle.get(key)

    def __iter__(self):
        """Returns an iterator for the keys the message contains."""
        return self.handle.__iter__()

    def unpack(self):
        """Decodes the data section of the message. When a message is unpacked all
        the keys in the data section become available via :obj:`metadata`.

        See Also
        --------
        :obj:`unpack`
        """
        return self.handle.unpack()

    def pack(self):
        """Encodes the data section of the message. Having called ``pack`` the
        contents of only the header keys become available via :obj:`metadata`. To access
        the data section you need to use :obj:`unpack` again.

        See Also
        --------
        :obj:`unpack`
        """
        return self.handle.unpack()

    def metadata(self, *keys, astype=None, **kwargs):
        r"""Returns metadata values from the BUFR message. When the message in packed
        (default state) only the header keys are available. To access the data section keys
        you need to call :obj:`unpack`.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying metadata keys. Only ecCodes BUFR keys can be used
            here. It can contain a single str or a list or tuple. Can be empty, in this case
            all the keys will
            be used.
        astype: type name, :obj:`list` or :obj:`tuple`
            Return types for ``keys``. A single value is accepted and applied to all the ``keys``.
            Otherwise, must have same the number of elements as ``keys``. Only used when
            ``keys`` is not empty.
        **kwargs: tuple, optional
            Other keyword arguments:

            * default: value, optional
                Specifies the same default value for all the ``keys`` specified. When ``default`` is
                **not present** and a key is not found or its value is a missing value
                :obj:`metadata` will raise KeyError.

        Returns
        -------
        single value, :obj:`list`, :obj:`tuple` or :obj:`dict`
            - when ``keys`` is not empty:
                - single value when ``keys`` is a str
                - otherwise the same type as that of ``keys`` (:obj:`list` or :obj:`tuple`)
            - when ``keys`` is empty:
                - returns a :obj:`dict` with one item per key

        Raises
        ------
        KeyError
            If no ``default`` is set and a key is not found in the message or it has a missing value.

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/temp_10.bufr")
        >>> ds[0].metadata("edition")
        3
        >>> ds[0].metadata("dataCategory", "dataSubCategory")
        (2, 101)

        """
        key, namespace, astype, key_arg_type = metadata_argument(
            *keys, namespace=None, astype=astype
        )

        assert isinstance(key, list)
        assert isinstance(namespace, (list, tuple))

        if key:
            assert isinstance(astype, (list, tuple))
            r = [self.handle.get(k, ktype=kt, **kwargs) for k, kt in zip(key, astype)]

            if key_arg_type == str:
                return r[0]
            elif key_arg_type == tuple:
                return tuple(r)
            else:
                return r
        else:
            return self.handle.as_namespace()

    def is_coord(self, key):
        """Check if the specified key is a BUFR coordinate descriptor

        Parameters
        ----------
        key: str
            Key name (can contain ecCodes rank)

        Returns
        -------
        bool
            True if the specified ``key`` is a BUFR coordinate descriptor
        """
        try:
            return bufr_code_is_coord(self.d[key + "->code"])
        except Exception:
            return False

    def dump(self, subset=1):
        r"""Generates a dump with the message content represented as a tree view in a Jupyter notebook.

        Parameters
        ----------
        subset: int
            Subset to dump. Please note that susbset indexing starts at 1. Use None to dump all the
            subsets in the message.

        Returns
        -------
        HTML
            Dump contents represented as a tree view in a Jupyter notebook.

        Examples
        --------
        :ref:`/examples/bufr_temp.ipynb`

        """
        from earthkit.data.core.temporary import temp_file

        with temp_file() as filename:
            self.handle.json_dump(filename)
            with open(filename, "r") as f:
                import json
                import warnings

                try:
                    d = json.loads(f.read())
                    return make_bufr_html_tree(
                        d,
                        self.__repr__(),
                        subset,
                        self.is_compressed(),
                        self.is_uncompressed(),
                    )
                except Exception as e:
                    warnings.warn("Failed to parse bufr_dump", e)
                    return None

    def write(self, f):
        r"""Writes the message to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        """
        self.handle.write_to(f)

    def message(self):
        r"""Returns a buffer containing the encoded message.

        Returns
        -------
        bytes
        """
        return self.handle.get_buffer()


class BUFRListMixIn(PandasMixIn):
    def ls(self, *args, **kwargs):
        r"""Generates a list like summary of the BUFR message list using a set of metadata keys.

        Parameters
        ----------
        n: int, None
            The number of :obj:`BUFRMEssage <data.readers.bufr.bufr.BUFRMessage>`\ s to be
            listed. ``None`` means all the messages, ``n > 0`` means messages from the front, while
            ``n < 0`` means messages from the back of the list.
        keys: list of str, dict, None
            Metadata keys. To specify a column title for each key in the output use a dict. If
            ``keys`` is None the following dict will be used to define the titles and the keys::

                {
                    "edition": "edition",
                    "type": "dataCategory",
                    "subtype": "dataSubCategory",
                    "c": "bufrHeaderCentre",
                    "mv": "masterTablesVersionNumber",
                    "lv": "localTablesVersionNumber",
                    "subsets": "numberOfSubsets",
                    "compr": "compressedData",
                    "typicalDate": "typicalDate",
                    "typicalTime": "typicalTime",
                    "ident": "ident",
                    "lat": "localLatitude",
                    "lon": "localLongitude",
                }

        extra_keys: list of str, dict, None
            List of additional keys to ``keys``. To specify a column title for each key in the output
            use a dict.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row per :obj:`BUFRMEssage <data.readers.bufr.bufr.BUFRMessage>`.

        Examples
        --------
        :ref:`/examples/bufr_temp.ipynb`

        """
        from earthkit.data.utils.summary import ls

        def _proc(keys, n):
            count_start = 0
            if n is None:
                count_end = len(self)
            elif n > 0:
                count_end = n
            else:
                num = len(self)
                count_start = max(0, num + n)
                count_end = num

            for count, msg in enumerate(self):
                if count_start <= count < count_end:
                    yield ({k: msg._header(k1) for k, k1 in keys.items()})
                elif count >= count_end:
                    break

        return ls(_proc, BUFR_LS_KEYS, *args, **kwargs)

    def head(self, n=5, **kwargs):
        r"""Generates a list like summary of the first ``n``
        :obj:`BUFRMEssage <data.readers.bufr.bufr.BUFRMessage>`\ s using a set of metadata keys.
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
        r"""Generates a list like summary of the last ``n``
        :obj:`BUFRMEssage <data.readers.bufr.bufr.BUFRMessage>`\ s using a set of metadata keys.
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

    def metadata(self, *args, **kwargs):
        r"""Returns the metadata values for each message.

        Parameters
        ----------
        *args: tuple
            Positional arguments defining the metadata keys. Passed to
            :obj:`BUFRMessage.metadata() <data.readers.bufr.bufr.BUFRMessage.metadata>`
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`BUFRMessage.metadata() <data.readers.bufr.bufr.BUFRMessage.metadata>`

        Returns
        -------
        list
            List with one item per :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage.metadata>`

        """
        result = []
        for s in self:
            result.append(s.metadata(*args, **kwargs))
        return result


class BUFRList(BUFRListMixIn, Index):
    r"""Represents a list of
    :obj:`BUFRMessage <data.readers.bufr.bufr.BUFRMessage>`\ s.
    """

    def __init__(self, *args, **kwargs):
        Index.__init__(self, *args, **kwargs)

    @classmethod
    def new_mask_index(self, *args, **kwargs):
        return MaskBUFRList(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(_, BUFRList) for _ in sources)
        return MultiBUFRList(sources)

    def sel(self, *args, **kwargs):
        """Uses header metadata values to select only certain messages from a BUFRList object.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the filter condition as dict.
            (See below for details).
        **kwargs: dict, optional
            Other keyword arguments specifying the filter conditions.
            (See below for details).

        Returns
        -------
        object
            Returns a new object with the filtered elements. It contains a view to the data in the
            original object, so no data is copied.


        Filter conditions are specified by a set of **metadata** keys either by a dictionary (in
        ``*args``) or a set of ``**kwargs``. Both single or multiple keys are allowed to use and each
        can specify the following type of filter values:

        - single value::

            ds.sel(dataCategory="2")

        - list of values::

            ds.sel(dataCategory=[1, 2])

        - **slice** of values (defines a **closed interval**, so treated as inclusive of both the start
        and stop values, unlike normal Python indexing)::

            # filter dataCategory between 1 and 4 inclusively
            ds.sel(dataCategory=slice(1,4))
        """
        kwargs.pop("remapping", None)
        return super().sel(*args, remapping=None, **kwargs)

    def isel(self, *args, **kwargs):
        raise NotImplementedError()

    def order_by(self, *args, **kwargs):
        """Changes the order of the messages in a BUFRList object.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to perform the ordering on.
            (See below for details)
        **kwargs: dict, optional
            Other keyword arguments specifying the metadata keys to perform the ordering on.
            (See below for details)

        Returns
        -------
        object
            Returns a new object with reordered messages. It contains a view to the data in the
            original object, so no data is copied.

        """
        kwargs.pop("remapping", None)
        return super().order_by(*args, remapping=None, **kwargs)


class MaskBUFRList(BUFRList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)


class MultiBUFRList(BUFRList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)


class BUFRInFiles(BUFRList):
    # Remote BUFRLists (with urls) are also here,
    # as the actual fieldlist is accessed on a file in cache.
    # This class changes the interface (__getitem__ and __len__)
    # into the interface (part and number_of_parts).
    def _getitem(self, n):
        if isinstance(n, int):
            part = self.part(n if n >= 0 else len(self) + n)
            return BUFRMessage(part.path, part.offset, part.length)

    def __len__(self):
        return self.number_of_parts()

    @abstractmethod
    def part(self, n):
        self._not_implemented()

    @abstractmethod
    def number_of_parts(self):
        self._not_implemented()


class BUFRInOneFile(BUFRInFiles):
    def __init__(self, path):
        self.path = path
        self.__positions = None

    @property
    def _positions(self):
        if self.__positions is None:
            self.__positions = BufrCodesMessagePositionIndex(self.path)
        return self.__positions

    def part(self, n):
        return Part(self.path, self._positions.offsets[n], self._positions.lengths[n])

    def number_of_parts(self):
        return len(self._positions)


class BUFRReader(BUFRInOneFile, Reader):
    """Represents a BUFR file"""

    appendable = True  # BUFR messages can be added to the same file

    def __init__(self, source, path):
        Reader.__init__(self, source, path)
        BUFRInOneFile.__init__(self, path)

    def __repr__(self):
        return "BUFRReader(%s)" % (self.path,)

    @classmethod
    def merge(cls, readers):
        assert all(isinstance(s, BUFRReader) for s in readers), readers
        assert len(readers) > 1

        return MultiBUFRList(readers)

    def mutate_source(self):
        # A BUFRReader is a source itself
        return self
