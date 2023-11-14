# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import warnings

from earthkit.data.utils.kwargs import Kwargs
from earthkit.data.utils.serialise import deserialise_state, serialise_state

LOG = logging.getLogger(__name__)


class ItemWrapperForCfGrib:
    def __init__(self, item, ignore_keys=[]):
        self.item = item
        self.ignore_keys = ignore_keys

    def __getitem__(self, n):
        if n in self.ignore_keys:
            return None
        if n == "values":
            return self.item.values
        return self.item.metadata(n)


class IndexWrapperForCfGrib:
    def __init__(self, index=None, ignore_keys=[]):
        self.index = index
        self.ignore_keys = ignore_keys

    def __getstate__(self):
        return dict(index=serialise_state(self.index), ignore_keys=self.ignore_keys)

    def __setstate__(self, state):
        self.index = deserialise_state(state["index"])
        self.ignore_keys = state["ignore_keys"]

    def __getitem__(self, n):
        return ItemWrapperForCfGrib(
            self.index[n],
            ignore_keys=self.ignore_keys,
        )

    def __len__(self):
        return len(self.index)


class XarrayMixIn:
    def xarray_open_dataset_kwargs(self):
        return dict(
            cache=True,  # Set to false to prevent loading the whole dataset
            chunks=None,  # Set to 'auto' for lazy loading
        )

    def to_xarray(self, **kwargs):
        """
        Convert the FieldList into an xarray DataSet using :xref:`cfgrib`.

        Parameters
        ----------
        **kwargs: dict, optional
            Other keyword arguments:

            xarray_open_dataset_kwargs: dict, optional
                Keyword arguments passed to ``xarray.open_dataset()``. Default value is::

                    {"backend_kwargs": {"errors": "raise"},
                    "squeeze": False, "cache": True, "chunks": None,
                    "errors": "raise", "engine": "cfgrib"}

                Please note that the settings ``errors="raise"`` and ``engine="cfgrib"`` are always
                enforced and cannot be changed.

        Returns
        -------
        xarray DataSet

        Examples
        --------
        >>> import earthkit.data
        >>> fs = earthkit.data.from_source("file", "test6.grib")
        >>> ds = fs.to_xarray(
        ...     xarray_open_dataset_kwargs={
        ...         "backend_kwargs": {"ignore_keys": ["number"]}
        ...     }
        ... )

        """
        import xarray as xr

        xarray_open_dataset_kwargs = {}

        if "xarray_open_mfdataset_kwargs" in kwargs:
            warnings.warn(
                "xarray_open_mfdataset_kwargs is deprecated, please use xarray_open_dataset_kwargs instead."
            )
            kwargs["xarray_open_dataset_kwargs"] = kwargs.pop(
                "xarray_open_mfdataset_kwargs"
            )

        user_xarray_open_dataset_kwargs = kwargs.get("xarray_open_dataset_kwargs", {})

        # until ignore_keys is included into cfgrib,
        # it is implemented here directly
        ignore_keys = user_xarray_open_dataset_kwargs.get("backend_kwargs", {}).pop(
            "ignore_keys", []
        )

        for key in ["backend_kwargs"]:
            xarray_open_dataset_kwargs[key] = Kwargs(
                user=user_xarray_open_dataset_kwargs.pop(key, {}),
                default={"errors": "raise"},
                forced={},
                logging_owner="xarray_open_dataset_kwargs",
                logging_main_key=key,
            )

        default = dict(squeeze=False)  # TODO:Documenet me
        default.update(self.xarray_open_dataset_kwargs())

        xarray_open_dataset_kwargs.update(
            Kwargs(
                user=user_xarray_open_dataset_kwargs,
                default=default,
                forced={
                    "errors": "raise",
                    "engine": "cfgrib",
                },
            )
        )

        result = xr.open_dataset(
            IndexWrapperForCfGrib(self, ignore_keys=ignore_keys),
            **xarray_open_dataset_kwargs,
        )

        return result
