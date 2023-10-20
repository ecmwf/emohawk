# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

import numpy as np

from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.wrappers import Wrapper

logger = logging.getLogger(__name__)


class PandasSeriesWrapper(Wrapper):
    """Wrapper around a `pandas.DataFrame`, offering polymorphism and
    convenience methods.
    """

    def __init__(self, data):
        self.data = data

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, i):
        return self.data.columns[i]

    def __len__(self):
        return len(self.data)

    def to_pandas(self):
        """
        Return a `pandas.Series` representation of the data.

        Returns
        -------
        pandas.Series
        """
        return self.data

    def to_numpy(self, **kwargs):
        """
        Return a `numpy.array` representation of the data.

        Returns
        -------
        numpy.array
        """
        return self.data.to_numpy(**kwargs)

    def to_xarray(self, **kwargs):
        """
        Return a `xarray.DataArray` representation of the data.

        Returns
        -------
        numpy.array
        """
        return self.data.to_xarray(**kwargs)

    def to_netcdf(self, *args, **kwargs):
        """
        Write the pandas object to a netCDF file

        Returns
        -------
        numpy.array
        """
        return self.data.to_xarray().to_netcdf(*args, **kwargs)

    def to_json(self, *args, **kwargs):
        """
        Write the pandas object to a netCDF file

        Returns
        -------
        numpy.array
        """
        kwargs.setdefault("indent", 2)
        return self.data.to_json(*args, **kwargs)

    def describe(self):
        """
        A pandas is tabular, therefore return itself

        Returns
        -------
        numpy.array
        """
        return self.data


class PandasDataFrameWrapper(PandasSeriesWrapper):
    """Wrapper around a `pandas.DataFrame`, offering polymorphism and
    convenience methods.
    """

    def to_pandas(self):
        """
        Return a `pandas.DataFrame` representation of the data.

        Returns
        -------
        pandas.DataFrame
        """
        return self.data

    def to_xarray(self, **kwargs):
        """
        Return a `xarray.Dataset` representation of the data.

        Returns
        -------
        numpy.array
        """
        return self.data.to_xarray(**kwargs)


class GeoPandasDataFrameWrapper(PandasDataFrameWrapper):
    """Wrapper around a `geopandas.DataFrame`, offering polymorphism and
    convenience methods.

    Key difference to a pandas dataframe wrapper, we treat rows (features) as fields
    """

    def __init__(self, source):
        super().__init__(source)
        try:
            (
                self.east,
                self.south,
                self.west,
                self.north,
            ) = self.data.crs.area_of_use.bounds
        except AttributeError:
            logger.warn("Bounding box not found in geopandas object")
            (
                self.east,
                self.south,
                self.west,
                self.north,
            ) = (np.nan, np.nan, np.nan, np.nan)
        self.fields = None

    def __iter__(self):
        """
        Iterate over features in geojson via pandas
        """
        self._scan()
        return iter(self.fields)

    def __getitem__(self, i):
        self._scan()
        return self.fields[i]

    def __len__(self):
        return len(self.data)

    def _scan(self):
        if self.fields is None:
            self.fields = self.get_fields()

    def get_fields(self):
        """
        For geopandas, a field is a feature
        """
        return [row[1] for row in self.data.iterrows()]

    def bounding_box(self):
        """
        For geopandas, get bounding box and convert to EK.BoundingBox type
        """
        return BoundingBox(
            north=self.north, south=self.south, east=self.east, west=self.west
        )


def wrapper(data, *args, **kwargs):
    import pandas as pd

    try:
        import geopandas as gpd

        l_gpd = True
    except ImportError:
        l_gpd = False

    if l_gpd and isinstance(data, gpd.geodataframe.GeoDataFrame):
        return GeoPandasDataFrameWrapper(data, *args, **kwargs)
    if isinstance(data, pd.DataFrame):
        return PandasDataFrameWrapper(data, *args, **kwargs)
    if isinstance(data, pd.Series):
        return PandasSeriesWrapper(data, *args, **kwargs)

    return None
