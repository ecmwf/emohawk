# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# The code is copied from skinnywms, and we should combile later

import mimetypes

import numpy as np

from earthkit.data.readers import Reader
from earthkit.data.wrappers.pandas import GeoPandasDataFrameWrapper


class GeojsonReader(Reader):
    def __init__(self, source, path):
        super().__init__(source, path)
        self.fields = None

    def _scan(self):
        """
        For geojson, a field is a feature
        """
        if self.fields is None:
            self.fields = self.get_fields()

    def __repr__(self):
        return f"GeojsonReader({self.path})"
        # return self.to_pandas().__repr__()

    def _repr_html_(self):
        html_repr = (
            f"<h3>GeojsonReader(represented as a geopandas object):</h3>"
            f"{self.to_pandas()._repr_html_()}"
        )

        return html_repr

    def __iter__(self):
        """
        Iterate over features in geojson via pandas
        """
        self._scan()
        return iter(self.fields)

    def __len__(self):
        self._scan()
        return len(self.fields)

    def __getitem__(self, n):
        self._scan()
        return self.fields[n]

    def mutate_source(self):
        # A Geojson is a source itself
        return self

    def bounding_box(self, **kwargs):
        return self._to_geopandas_dataframe_wrapper(**kwargs).bounding_box()

    def ls(self, **kwargs):
        return self.to_pandas(**kwargs)

    def describe(self, **kwargs):
        return self.to_pandas(**kwargs)

    def get_fields(self, **kwargs):
        return [row[1] for row in self.to_pandas(**kwargs).iterrows()]

    def to_numpy(self, flatten=False):
        arr = self.to_pandas().to_numpy()
        if flatten:
            arr = arr.flatten()
        return arr

    def to_pandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas_from_multi_paths([self.path], **kwargs)

    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self.to_pandas(**kwargs).to_xarray()

    @classmethod
    def to_pandas_from_multi_paths(cls, paths, **kwargs):
        import geopandas as gpd

        geo_df = gpd.pd.concat([gpd.read_file(path, **kwargs) for path in paths])

        return geo_df.set_index(np.arange(len(geo_df)))

    def _to_geopandas_dataframe_wrapper(self, **kwargs):
        return GeoPandasDataFrameWrapper(self.to_pandas(**kwargs))


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    kind, compression = mimetypes.guess_type(path)
    ext = path.split(".")[-1]

    geojson_extensions = ["geojson"]
    geojson_mimetypes = ["application/geo+json"]
    if magic is None or ext in geojson_extensions or kind in geojson_mimetypes:
        return GeojsonReader(source, path)
