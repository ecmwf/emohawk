# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


PROJ_PARAMS_TO_KWARGS = {
    "lon_0": "central_longitude",
    "lat_0": "central_latitude",
    "lat_ts": "true_scale_latitude",
    "x_0": "false_easting",
    "y_0": "false_northing",
    "k": "scale_factor",
    "zone": "zone",
    "proj": "proj_name",
}

STANDARD_PARALLELS = ["lat_1", "lat_2"]

PROJ_PARAMS_TO_GLOBE_KWARGS = {
    "a": "semimajor_axis",
    "b": "semiminor_axis",
    "datum": "datum",
    "ellps": "ellipse",
    "f": "flattening",
    "rf": "inverse_flattening",
}


def to_dict(proj_string):
    proj_params = {
        k.lstrip("+"): v
        for k, v in (
            p.split("=") if "=" in p else (p, None) for p in proj_string.split()
        )
    }

    for key, value in proj_params.items():
        try:
            proj_params[key] = float(value)
        except (TypeError, ValueError):
            continue

    return proj_params


def to_projection_kwargs(proj_params):
    if isinstance(proj_params, str):
        proj_params = to_dict(proj_params)
    proj_params.pop("proj", None)  # remove the projection name

    globe_params = {
        PROJ_PARAMS_TO_GLOBE_KWARGS[param]: proj_params.pop(param)
        for param in PROJ_PARAMS_TO_GLOBE_KWARGS
        if param in proj_params
    }

    kwargs = {
        PROJ_PARAMS_TO_KWARGS[k]: v
        for k, v in proj_params.items()
        if k in PROJ_PARAMS_TO_KWARGS
    }
    kwargs["globe"] = globe_params

    standard_parallels = tuple(
        proj_params[param] for param in STANDARD_PARALLELS if param in proj_params
    )
    if standard_parallels:
        kwargs["standard_parallels"] = standard_parallels

    return kwargs
