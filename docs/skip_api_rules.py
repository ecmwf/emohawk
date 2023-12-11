# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

_skip_methods = {
    "data.readers.bufr.bufr.BUFRList": [
        "cache_file",
        "dataset",
        "from_dict",
        "from_mask",
        "from_multi",
        "from_slice",
        "full",
        "graph",
        "ignore",
        "merge",
        "mutate",
        "new_mask_index",
        "parent",
        "settings",
        "to_numpy",
    ],
    "data.readers.bufr.bufr.BUFRMessage": ["merge", "mutate", "to_numpy"],
    "data.readers.grib.codes.GribField": ["merge", "mutate"],
    "data.core.fieldlist.FieldList": [
        "cache_file",
        "dataset",
        "from_dict",
        "from_mask",
        "from_multi",
        "from_slice",
        "full",
        "graph",
        "ignore",
        "merge",
        "mutate",
        "new_mask_index",
        "parent",
        "scaled",
        "settings",
        "statistics",
        "xarray_open_dataset_kwargs",
    ],
    "data.readers.grib.index.GribFieldList": [
        "cache_file",
        "dataset",
        "from_dict",
        "from_mask",
        "from_multi",
        "from_slice",
        "full",
        "graph",
        "ignore",
        "merge",
        "mutate",
        "new_mask_index",
        "parent",
        "scaled",
        "settings",
        "statistics",
        "xarray_open_dataset_kwargs",
    ],
    "data.readers.csv.CSVReader": [
        "bounding_box",
        "cache_file",
        "to_numpy",
        "ignore",
        "datetime",
        "index_content",
        "isel",
        "merge",
        "metadata",
        "mutate",
        "mutate_source",
        "order_by",
        "sel",
        "filter",
        "merger",
        "source",
    ],
    "data.source.numpy_list.NumpyField": ["merge", "mutate"],
    "data.source.numpy_list.NumpyFieldList": [
        "cache_file",
        "dataset",
        "from_dict",
        "from_mask",
        "from_multi",
        "from_slice",
        "full",
        "graph",
        "ignore",
        "merge",
        "mutate",
        "new_mask_index",
        "parent",
        "scaled",
        "settings",
        "statistics",
        "xarray_open_dataset_kwargs",
    ],
}


# define skip rules for autoapi
def _skip_api_items(app, what, name, obj, skip, options):
    # if what == "package":
    #     print(f"{name}[{what}]")

    if what == "module" and name not in [
        "data.core",
        "data.core.caching",
        "data.core.metadata",
        "data.core.fieldlist",
        "data.readers",
        "data.readers.bufr.bufr",
        "data.readers.grib.codes",
        "data.readers.grib.index",
        "data.readers.csv",
        "data.sources",
        "data.sources.numpy_list",
        "data.utils",
        "data.utils.bbox",
    ]:
        skip = True
    elif what == "package" and name not in [
        "data",
        "data.core",
        "data.core.caching",
        "data.readers",
        "data.readers.bufr",
        "data.readers.bufr.bufr",
        "data.readers.grib",
        "data.readers.grib.index",
        "data.readers.csv",
        "data.sources",
        "data.sources.numpy_list",
        "data.utils",
        "data.utils.bbox",
    ]:
        skip = True
    elif what == "class" and name not in [
        "data.core.caching.Cache",
        "data.core.fieldlist.Field",
        "data.core.fieldlist.FieldList",
        "data.core.metadata.Metadata",
        "data.core.metadata.RawMetadata",
        "data.readers.bufr.bufr.BUFRList",
        "data.readers.bufr.bufr.BUFRMessage",
        "data.readers.grib.codes.GribField",
        "data.readers.grib.index.GribFieldList",
        "data.readers.grib.metadata.GribMetadata",
        "data.readers.csv.CSVReader",
        "data.sources.numpy_list.NumpyField",
        "data.sources.numpy_list.NumpyFieldList",
        "data.utils.bbox.BoundingBox",
    ]:
        skip = True
    elif what == "method":
        # if "abstractmethod" in getattr(obj, "properties", []):
        #     skip = True
        # else:
        if True:
            for k, v in _skip_methods.items():
                if k in name and name.split(".")[-1] in v:
                    skip = True
                    break

    elif what in ("function", "attribute", "data"):
        skip = True

    # if not skip:
    #     print(f"{what} {name}")
    return skip
