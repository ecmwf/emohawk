# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import json
import logging
import warnings

from emohawk.core.caching import auxiliary_cache_file
from emohawk.core.index import ScaledIndex
from emohawk.utils.bbox import BoundingBox

from .pandas import PandasMixIn

# from .pytorch import PytorchMixIn
# from .tensorflow import TensorflowMixIn
from .xarray import XarrayMixIn

LOG = logging.getLogger(__name__)


class FieldSetMixin(PandasMixIn, XarrayMixIn):
    _statistics = None

    def _find_coord_values(self, key):
        values = []
        for i in self:
            v = i.metadata(key)
            if v not in values:
                values.append(v)
        return tuple(values)

    def coord(self, key):
        if key in self._coords:
            return self._coords[key]

        self._coords[key] = self._find_coord_values(key)
        return self.coord(key)

    def _find_coords_keys(self):
        from emohawk.indexing.database.sql import GRIB_INDEX_KEYS

        return GRIB_INDEX_KEYS

    def _find_all_coords_dict(self, squeeze):
        out = {}
        for key in self._find_coords_keys():
            values = self.coord(key)
            if squeeze and len(values) == 1:
                continue
            if len(values) == 0:
                # This should never happen
                warnings.warn(f".coords warning: GRIB key not found {key}")
                continue
            out[key] = values
        return out

    @property
    def coords(self):
        return self._find_all_coords_dict(squeeze=True)

    @property
    def first(self):
        return self[0]

    def to_numpy(self, **kwargs):
        import numpy as np

        return np.array([f.to_numpy(**kwargs) for f in self])

    @property
    def values(self):
        import numpy as np

        return np.array([f.values for f in self])

    def metadata(self, *args, **kwargs):
        result = []
        for s in self:
            result.append(s.metadata(*args, **kwargs))
        return result

    def ls(self, extra_keys=None, **kwargs):
        from emohawk.utils.summary import GRIB_LS_KEYS, format_ls

        keys = list(GRIB_LS_KEYS)
        extra_keys = [] if extra_keys is None else extra_keys
        if extra_keys is not None:
            [keys.append(x) for x in extra_keys if x not in keys]

        def _proc():
            for f in self:
                yield (f._attributes(keys))

        return format_ls(_proc(), **kwargs)

    def describe(self, *args, **kwargs):
        from emohawk.utils.summary import GRIB_DESCRIBE_KEYS, format_describe

        def _proc():
            for f in self:
                yield (f._attributes(GRIB_DESCRIBE_KEYS))

        return format_describe(_proc(), *args, **kwargs)

    # Used by normalisers
    def to_datetime(self):
        times = self.to_datetime_list()
        assert len(times) == 1
        return times[0]

    def to_datetime_list(self):
        # TODO: check if that can be done faster
        result = set()
        for s in self:
            result.add(s.valid_datetime())
        return sorted(result)

    def to_bounding_box(self):
        return BoundingBox.multi_merge([s.to_bounding_box() for s in self])

    def statistics(self):
        import numpy as np

        if self._statistics is not None:
            return self._statistics

        if False:
            cache = auxiliary_cache_file(
                "grib-statistics--",
                self.path,
                content="null",
                extension=".json",
            )

            with open(cache) as f:
                self._statistics = json.load(f)

            if self._statistics is not None:
                return self._statistics

        stdev = None
        average = None
        maximum = None
        minimum = None
        count = 0

        for s in self:
            v = s.values
            if count:
                stdev = np.add(stdev, np.multiply(v, v))
                average = np.add(average, v)
                maximum = np.maximum(maximum, v)
                minimum = np.minimum(minimum, v)
            else:
                stdev = np.multiply(v, v)
                average = v
                maximum = v
                minimum = v

            count += 1

        nans = np.count_nonzero(np.isnan(average))
        assert nans == 0, "Statistics with missing values not yet implemented"

        maximum = np.amax(maximum)
        minimum = np.amin(minimum)
        average = np.mean(average) / count
        stdev = np.sqrt(np.mean(stdev) / count - average * average)

        self._statistics = dict(
            minimum=minimum,
            maximum=maximum,
            average=average,
            stdev=stdev,
            count=count,
        )

        if False:
            with open(cache, "w") as f:
                json.dump(self._statistics, f)

        return self._statistics

    def save(self, filename):
        with open(filename, "wb") as f:
            self.write(f)

    def write(self, f):
        for s in self:
            s.write(f)

    def scaled(self, method=None, offset=None, scaling=None):
        if method == "minmax":
            assert offset is None and scaling is None
            stats = self.statistics()
            offset = stats["minimum"]
            scaling = 1.0 / (stats["maximum"] - stats["minimum"])

        return ScaledIndex(self, offset, scaling)
