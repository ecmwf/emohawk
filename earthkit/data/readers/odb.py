# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import Reader

LOG = logging.getLogger(__name__)


class ODBReader(Reader):
    def to_pandas(self, **kwargs):
        try:
            import codc as odc
        except Exception:
            import pyodc as odc

            LOG.debug("Using pure Python odc decoder.")

        odc_read_odb_kwargs = kwargs.get("odc_read_odb_kwargs", {})
        return odc.read_odb(self.path, single=True, **odc_read_odb_kwargs)


def _match_magic(magic, deeper_check):
    if magic is not None:
        type_id = b"\xff\xffODA"
        if not deeper_check:
            return len(magic) >= 5 and magic[:5] == type_id
        else:
            return type_id in magic
    return False


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    if _match_magic(magic, deeper_check):
        return ODBReader(source, path)
