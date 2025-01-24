# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from __future__ import annotations

import logging
import math
import os
from typing import TYPE_CHECKING

from . import SimpleTarget

LOG = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing import Any
    from typing import Dict

    from multio import Multio
    from multio.plans import Client


class MultioTarget(SimpleTarget):
    _server: Multio = None

    def __init__(self, plan: Client | os.PathLike | str | Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.plan = plan

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        pass

    def _write(self, data, **kwargs):
        encoder = "multio"
        kwargs.pop("encoder", None)
        kwargs.pop("plan", None)

        r = self._encode(data, encoder=encoder, **kwargs)
        if hasattr(r, "__iter__"):
            for d in r:
                self._add(d)
        else:
            self._add(r)

    def _add(self, d):
        array = d.to_array()
        metadata = d.metadata()
        metadata.update(
            {
                "globalSize": math.prod(array.shape),
            }
        )

        import multio

        with multio.MultioPlan(self.plan):
            server = multio.Multio()

            server_metadata = multio.Metadata(server, metadata)
            server.write_field(server_metadata, array)

    def _write_reader(self, reader, **kwargs):
        raise NotImplementedError


target = MultioTarget
