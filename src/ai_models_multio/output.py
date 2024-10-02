# (C) Copyright 2024 European Centre for Medium-Range Weather Forecasts.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from __future__ import annotations

from typing import TYPE_CHECKING

from functools import cached_property
from typing import Any
from ai_models.outputs import Output
import math

import multiopython
from contextlib import redirect_stdout
import io

if TYPE_CHECKING:
    from earthkit.data.core.metadata import Metadata

from .plans import get_plan, PLANS

def earthkit_to_multio(metadata: Metadata):
    """
    Convert EarthKit metadata to Multio metadata
    """
    metad = metadata.as_namespace("mars")
    metad.pop("levtype", None)

    metad["paramId"] = metadata["paramId"]
    metad["typeOfLevel"] = metadata["typeOfLevel"]

    return metad


class MultioOutput(Output):
    def __init__(self, owner, path, metadata, plan: PLANS = "to_file", **kwargs):
        """
        Multio Output plugin for ai-models
        """

        multio_plan = get_plan(plan, output_path=path)

        self.owner = owner
        self.path = path

        metadata.setdefault("stream", "oper")
        metadata.setdefault("expver", owner.expver)
        metadata.setdefault("class", "ml")

        self.metadata = metadata

        with multiopython.MultioPlan(multio_plan):
            self.server = multiopython.Multio()
        # self.server.start_server() # Pointer error

    def write(self, data, *args, check_nans=False, **kwargs):
        """
        Write data to multio
        """

        # Skip if data is None
        if data is None:
            return
        
        template = kwargs.pop("template")
        step = kwargs.pop("step")

        metadata_template = dict(earthkit_to_multio(template.metadata()))
        metadata_template.update(self.metadata)
        metadata_template.update(kwargs)

        metadata_template.update({
            'step': step,
            'trigger': 'step',
            'type': 'fc',
            'globalSize': math.prod(data.shape)
        })


        with self.server as server:
            server_metadata = multiopython.Metadata(server, metadata_template)
            server.write_field(server_metadata, data)
            server.notify(server_metadata)


class FDBMultioOutput(MultioOutput):
    """Output directly to the FDB"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, plan="to_fdb", **kwargs)


class MultioDebugOutput(MultioOutput):
    """Debug"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, plan="debug", **kwargs)
