# (C) Copyright 2024 European Centre for Medium-Range Weather Forecasts.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import multiopython
from ai_models.model import Timer
from ai_models.outputs import Output

if TYPE_CHECKING:
    import numpy as np
    from earthkit.data.core.metadata import Metadata

from .plans import PLANS
from .plans import get_plan


def earthkit_to_multio(metadata: Metadata):
    """Convert earthkit metadata to Multio metadata"""
    metad = metadata.as_namespace("mars")
    metad.pop("levtype", None)
    metad.pop("param", None)

    metad["paramId"] = metadata["paramId"]
    metad["typeOfLevel"] = metadata["typeOfLevel"]

    return metad


class MultioOutput(Output):
    _server: multiopython.Multio = None

    def __init__(self, owner, path: str, metadata: dict, plan: PLANS = "to_file", **_):
        """Multio Output plugin for ai-models"""

        self._plan_name = plan
        self._path = path
        self._owner = owner

        metadata.setdefault("stream", "oper")
        metadata.setdefault("expver", owner.expver)
        metadata.setdefault("class", "ml")
        metadata.setdefault("gribEdition", "2")

        self.metadata = metadata

    def get_plan(self, data: np.ndarray, metadata: Metadata) -> multiopython.plans.Config:
        """Get the plan for the output"""
        return get_plan(self._plan_name, values=data, metadata=metadata, output_path=self._path)

    def server(self, data: np.ndarray, metadata: Metadata) -> multiopython.Multio:
        """Get multio server, with plan configured from data, metadata and path"""
        if self._server is None:
            with Timer("Multio server initialisation"):
                with multiopython.MultioPlan(self.get_plan(data, metadata)):
                    server = multiopython.Multio()
                    self._server = server
        return self._server

    def write(self, data: np.ndarray, *, check_nans: bool = False, **kwargs):
        """Write data to multio"""

        # Skip if data is None
        if data is None:
            return

        template_metadata: Metadata = kwargs.pop("template").metadata()
        step: int = kwargs.pop("step")

        metadata_template = dict(earthkit_to_multio(template_metadata))
        metadata_template.update(self.metadata)
        metadata_template.update(kwargs)

        metadata_template.update(
            {
                "step": step,
                "trigger": "step",
                "type": "fc",
                "globalSize": math.prod(data.shape),
                "generatingProcessIdentifier": self._owner.version,
            }
        )

        with self.server(data, template_metadata) as server:
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
