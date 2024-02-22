# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from . import cf, proj

try:
    import cartopy.crs as ccrs

    NO_CARTOPY = False
except ImportError:
    NO_CARTOPY = True
CARTOPY_WARNING = (
    "no cartopy installation found; cartopy must be installed to use this feature"
)


DEFAULT_LATLON_PROJ_STRING = (
    "+proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to_meter=111319.4907932736 "
    "+no_defs +type=crs"
)


class Projection:
    @classmethod
    def from_proj_string(cls, proj_string):
        if proj_string is None:
            proj_string = DEFAULT_LATLON_PROJ_STRING

        proj_params = proj.to_dict(proj_string)

        try:
            proj_name = proj_params["proj"]
        except KeyError:
            raise ValueError("proj string missing required parameter 'proj'")

        for cls in _PROJECTIONS:
            if cls.PROJ_NAME == proj_name:
                break
        else:
            raise ValueError(f"proj projection '{proj_name}' is not supported")

        kwargs = proj.to_projection_kwargs(proj_params)

        return cls(proj_string, **kwargs)

    @classmethod
    def from_cf_grid_mapping(cls, grid_mapping_name, **parameters):
        proj_string = parameters.pop("proj4_params", None)
        if proj_string is not None:
            return Projection.from_proj_string(proj_string)

        for cls in _PROJECTIONS:
            if cls.CF_GRID_MAPPING_NAME == grid_mapping_name:
                break
        else:
            raise ValueError(f"grid mapping '{grid_mapping_name}' is not supported")

        kwargs = cf.to_projection_kwargs(parameters)

        return cls(proj_string=proj_string, **kwargs)

    def __init__(self, proj_string=None, **kwargs):
        self.parameters = kwargs
        self.globe = self.parameters.pop("globe", dict())
        self._proj_string = proj_string

    def __repr__(self):
        if not NO_CARTOPY:
            return self.to_cartopy_crs().__repr__()
        else:
            return self.__str__()

    def __str__(self):
        return self.to_proj_string()

    def to_proj_string(self):
        if self._proj_string is None:
            raise ValueError("projection source provided no proj string")
        return self._proj_string

    def to_cartopy_globe(self):
        if NO_CARTOPY:
            raise ImportError(CARTOPY_WARNING)
        return ccrs.Globe(**self.globe)

    def to_cartopy_crs(self):
        if NO_CARTOPY:
            raise ImportError(CARTOPY_WARNING)
        return getattr(ccrs, self.CARTOPY_CRS)(
            globe=self.to_cartopy_globe(),
            **self.parameters,
        )


class EquidistantCylindrical(Projection):
    PROJ_NAME = "eqc"
    CF_GRID_MAPPING_NAME = "latitude_longitude"
    CARTOPY_CRS = "PlateCarree"


class LongLat(Projection):
    PROJ_NAME = "longlat"
    CF_GRID_MAPPING_NAME = "latitude_longitude"
    CARTOPY_CRS = "PlateCarree"


class LambertAzimuthalEqualArea(Projection):
    PROJ_NAME = "laea"
    CF_GRID_MAPPING_NAME = "lambert_azimuthal_equal_area"
    CARTOPY_CRS = "LambertAzimuthalEqualArea"


class LambertConformal(Projection):
    PROJ_NAME = "lcc"
    CF_GRID_MAPPING_NAME = "lambert_conformal_conic"
    CARTOPY_CRS = "LambertConformal"


class AlbersEqualArea(Projection):
    PROJ_NAME = "aea"
    CF_GRID_MAPPING_NAME = "albers_conical_equal_area"
    CARTOPY_CRS = "AlbersEqualArea"


class Mercator(Projection):
    PROJ_NAME = "merc"
    CF_GRID_MAPPING_NAME = "mercator"
    CARTOPY_CRS = "Mercator"


_PROJECTIONS = [
    EquidistantCylindrical,
    LongLat,
    LambertAzimuthalEqualArea,
    LambertConformal,
    AlbersEqualArea,
    Mercator,
]
