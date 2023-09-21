# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Import and path setup ---------------------------------------------------

import datetime
import os
import sys

sys.path.insert(0, os.path.abspath("./"))
sys.path.insert(0, os.path.abspath("../"))

# -- Project information -----------------------------------------------------

project = "earthkit-data"
author = "European Centre for Medium Range Weather Forecasts"

year = datetime.datetime.now().year
years = "2022-%s" % (year,)
copyright = "%s, European Centre for Medium-Range Weather Forecasts (ECMWF)" % (years,)

# version = earthkit.data.__version__
# release = earthkit.data.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "autoapi.extension",
    "earthkit.data.sphinxext.xref",
    "earthkit.data.sphinxext.module_output",
]

# autodoc configuration
autodoc_typehints = "none"

# autoapi configuration
autoapi_dirs = ["../earthkit/data"]
autoapi_ignore = ["*/version.py", "sphinxext/*"]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
    "inherited-members",
]
autoapi_root = "_api"
autoapi_member_order = "alphabetical"
autoapi_add_toctree_entry = False

# napoleon configuration
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_preprocess_types = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The suffix of source filenames.
source_suffix = ".rst"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["style.css"]

html_logo = "_static/earthkit-data.png"

xref_links = {
    "cfgrib": ("cfgirb", "https://github.com/ecmwf/cfgrib"),
    "eccodes": (
        "ecCodes",
        "https://confluence.ecmwf.int/display/ECC/ecCodes+Home",
    ),
    "eccodes_namespace": (
        "ecCodes namespace",
        "https://confluence.ecmwf.int/display/UDOC/What+are+namespaces+-+ecCodes+GRIB+FAQ",
    ),
    "pdbufr": ("pdbufr", "https://github.com/ecmwf/pdbufr"),
    "read_bufr": (
        "pdbufr.read_bufr()",
        "https://pdbufr.readthedocs.io/en/latest/read_bufr.html",
    ),
    "odb": ("ODB", "https://odc.readthedocs.io/en/latest/content/introduction.html"),
    "pyodc": ("pyodc", "https://github.com/ecmwf/pyodc"),
}


intersphinx_mapping = {"pandas": ("https://pandas.pydata.org/docs/", None)}


def setup(app):
    from skip_api_rules import _skip_api_items

    app.connect("autoapi-skip-member", _skip_api_items)
