# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.metadata import Metadata
from earthkit.data.core.metadata import WrappedMetadata


class SimpleFieldList(FieldList):
    def __init__(self, fields=None):
        self.fields = fields if fields is not None else []

    def append(self, field):
        self.fields.append(field)

    def _getitem(self, n):
        return self.fields[n]

    def __len__(self):
        return len(self.fields)

    def __repr__(self) -> str:
        return f"FieldArray({len(self.fields)})"

    def __getstate__(self) -> dict:
        ret = {}
        ret["_fields"] = self.fields
        return ret

    def __setstate__(self, state: dict):
        self.fields = state.pop("_fields")

    def to_pandas(self, *args, **kwargs):
        # TODO make it generic
        if len(self) > 0:
            if self[0]._metadata.data_format() == "grib":
                from earthkit.data.readers.grib.pandas import PandasMixIn

                class _C(PandasMixIn, SimpleFieldList):
                    pass

                return _C(self.fields).to_pandas(*args, **kwargs)
        else:
            import pandas as pd

            return pd.DataFrame()

    def to_xarray(self, *args, **kwargs):
        # TODO make it generic
        if len(self) > 0:
            if self[0]._metadata.data_format() == "grib":
                from earthkit.data.readers.grib.xarray import XarrayMixIn

                class _C(XarrayMixIn, SimpleFieldList):
                    pass

                return _C(self.fields).to_xarray(*args, **kwargs)
        else:
            import xarray as xr

            return xr.Dataset()

    def mutate_source(self):
        return self

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        assert len(args) == 2
        fs = args[0]
        indices = list(args[1])
        return cls.from_fields([fs.fields[i] for i in indices])

    @classmethod
    def merge(cls, sources):
        if not all(isinstance(_, SimpleFieldList) for _ in sources):
            raise ValueError("SimpleFieldList can only be merged to another SimpleFieldLists")

        from itertools import chain

        return cls.from_fields(list(chain(*[f for f in sources])))


class WrappedField:
    def __init__(self, field):
        self._field = field

    def __getattr__(self, name):
        return getattr(self._field, name)

    def __repr__(self) -> str:
        return repr(self._field)


class ClonedFieldCore:
    def __init__(self, field, values=None, metadata=None, **kwargs):
        self._field = field
        self.__values = values

        if metadata is not None:
            if isinstance(metadata, dict):
                metadata = dict(**metadata)
            elif isinstance(metadata, (Metadata, WrappedMetadata)):
                if kwargs:
                    raise ValueError("metadata and kwargs cannot be used together")
            else:
                raise ValueError(
                    "metadata must be a dict, Metadata or WrappedMetadata, got %s" % type(metadata)
                )

        if metadata is None:
            metadata = dict()

        assert metadata is not None

        if kwargs:
            if isinstance(metadata, dict):
                metadata.update(kwargs)

        if metadata:
            if isinstance(metadata, dict):
                self.__metadata = WrappedMetadata(field._metadata, extra=metadata, owner=field)
            else:
                self.__metadata = metadata
        else:
            self.__metadata = field._metadata

    def _values(self, dtype=None):
        if self.__values is None:
            return self._field._values(dtype=dtype)
        else:
            if dtype is None:
                return self.__values
            return self.__values.astype(dtype)

    @property
    def _metadata(self):
        return self.__metadata

    def _has_new_values(self):
        return self._values

    @property
    def handle(self):
        return self._metadata._handle

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        md = {}
        # wrapped metadata
        if hasattr(self._metadata, "extra"):
            md = {k: self._metadata._extra_value(k) for k, v in self._metadata.extra.items()}

        metadata = kwargs.pop("metadata", {})
        metadata.update(md)

        values = kwargs.pop("values", None)
        if values is None:
            values = self._values()

        return encoder._encode_field(self, values=values, metadata=metadata, **kwargs)


# For backwards compatibility
FieldArray = SimpleFieldList
