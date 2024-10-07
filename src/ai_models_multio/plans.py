# (C) Copyright 2024 European Centre for Medium-Range Weather Forecasts.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Literal

from multiopython.plans import Config
from multiopython.plans import Plan
from multiopython.plans import actions
from multiopython.plans import sinks

PLANS = Literal["to_file", "to_fdb", "debug"]

if TYPE_CHECKING:
    import numpy as np
    from earthkit.data.core.metadata import Metadata

LOG = logging.getLogger(__name__)


class CONFIGURED_PLANS:
    """Configured plans for Multio Output"""

    @staticmethod
    def to_file(output_path: os.PathLike, template_path: os.PathLike, grid_type: str = "n320", **_) -> Config:
        return Plan(
            actions=[
                actions.Encode(template=str(template_path), format="grib", grid_type=grid_type),
                actions.Sink(
                    sinks=[
                        sinks.File(
                            path=output_path,
                            append=True,
                            per_server=False,
                        )
                    ]
                ),
            ],
            name="output-to-file",
        ).to_config()

    @staticmethod
    def to_fdb(output_path: os.PathLike, template_path: os.PathLike, grid_type: str = "n320", **_) -> Config:
        return Plan(
            actions=[
                actions.Encode(template=str(template_path), format="grib", grid_type=grid_type),
                actions.Sink(sinks=[sinks.FDB()]),
            ],
            name="output-to-fdb",
        ).to_config()

    @staticmethod
    def debug(output_path: os.PathLike, **_) -> Config:
        return Plan(
            actions=[actions.Print(stream="cout", prefix=" ++ MULTIO-PRINT-ALL-DEBUG :: ")],
            name="output-to-file",
        ).to_config()


def get_template_path(values: np.ndarray, metadata: Metadata) -> str:
    """Get path to the template file

    Uses earthkit.data.readers.grib.output.GribCoder to determine the template file

    Pulls from in order:
        - ai_models_multio/templates
        - $ECCODES_DIR/share/eccodes/samples
        and fails over to the default template

    Returns
    -------
    str
        Path to the template file
    """
    from earthkit.data.readers.grib.output import GribCoder

    coder = GribCoder()
    metadata = dict(metadata)
    metadata["edition"] = metadata.get("gribEdition", 2)

    if len(values.shape) == 1:
        template_name = coder._gg_field(values, metadata)
    elif len(values.shape) == 2:
        template_name = coder._ll_field(values, metadata)
    else:
        warnings.warn(f"Invalid shape {values.shape} for GRIB, must be 1 or 2 dimension ", RuntimeWarning)
        template_name = "default"

    template_path = (Path(__file__).parent / "templates" / (template_name + ".tmpl")).absolute()

    if not template_path.exists():
        if "ECCODES_DIR" in os.environ:
            template_path = (
                Path(os.environ["ECCODES_DIR"]) / "share" / "eccodes" / "samples" / (template_name + ".tmpl")
            )
        else:
            warnings.warn(f"Template {template_path} does not exist, using default template", RuntimeWarning)
            template_path = Path(__file__).parent / "templates" / "default.tmpl"

    LOG.info(f"Using template {template_path!r}")

    return str(template_path.absolute())


def get_plan(plan: PLANS, values: np.ndarray, metadata: Metadata, **kwargs) -> Config:
    """Get plan for Multio Output

    Parameters
    ----------
    plan : PLANS
        Plan ID to get
    values : np.ndarray
        Values to find template from
    metadata : Metadata
        Metadata for the values, used to determine the template
    kwargs : dict
        Additional parameters for the plan

    Returns
    -------
    Config
        Multio Plan configuration
    """
    template_path = get_template_path(values, metadata)
    return getattr(CONFIGURED_PLANS, plan)(template_path=template_path, **kwargs)
