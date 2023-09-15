# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os

LOG = logging.getLogger(__name__)


_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def earthkit_conf_file(*args):
    return os.path.join(_ROOT_DIR, "earthkit", "data", "data", *args)
