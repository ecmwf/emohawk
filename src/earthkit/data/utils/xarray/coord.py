# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

LOG = logging.getLogger(__name__)


class Coord:
    def __init__(self, name, vals, dims=None, ds=None):
        self.name = name
        self.vals = vals
        self.dims = dims
        if not self.dims:
            self.dims = (self.name,)
        self.convert()

    @staticmethod
    def make(name, *args, **kwargs):
        if name in ["date", "valid_datetime", "base_datetime"]:
            return DateTimeCoord(name, *args, **kwargs)
        elif name in ["step"]:
            return StepCoord(name, *args, **kwargs)
        elif name in ["level", "levelist"]:
            return LevelCoord(name, *args, **kwargs)
        return Coord(name, *args, **kwargs)

    def make_var(self, profile):
        import xarray

        c = profile.rename_coords({self.name: None})
        name = list(c.keys())[0]
        return xarray.Variable(profile.rename_dims(self.dims), self.convert(), self.attrs(name, profile))

    def convert(self):
        return self.vals

    def attrs(self, name, profile):
        return profile.add_coord_attrs(name)


class DateTimeCoord(Coord):
    def convert(self):
        if isinstance(self.vals, list):
            from earthkit.data.utils.dates import to_datetime_list

            return to_datetime_list(self.vals)
        return super().convert()


class StepCoord(Coord):
    def convert(self):
        from earthkit.data.utils.dates import step_to_delta

        return [step_to_delta(x) for x in self.vals]


class LevelCoord(Coord):
    def __init__(self, name, vals, dims=None, ds=None):
        self.levtype = {}
        if ds is not None:
            for k in ["levtype", "typeOfLevel"]:
                if k in ds.indices():
                    self.levtype[k] = ds.index(k)[0]
                else:
                    v = ds[0].metadata(k, default=None)
                    if v is not None:
                        self.levtype[k] = v

        super().__init__(name, vals, dims)

    def attrs(self, name, profile):
        return profile.add_level_coord_attrs(name, self.levtype)
