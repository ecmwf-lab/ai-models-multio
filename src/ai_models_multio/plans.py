# (C) Copyright 2024 European Centre for Medium-Range Weather Forecasts.
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from multiopython.plans import Config
from multiopython.plans import Plan
from multiopython.plans import actions
from multiopython.plans import sinks

PLANS = Literal["to_file", "to_fdb", "debug"]

template_path = Path(__file__).parent / "templates" / "template.grib"


class CONFIGURED_PLANS:
    """Configured plans for Multio Output"""

    @staticmethod
    def to_file(output_path: os.PathLike, grid_type: str = "n320", **_) -> Config:
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
    def to_fdb(output_path: os.PathLike, grid_type: str = "n320", **_) -> Config:
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


def get_plan(plan: PLANS, **kwargs) -> Config:
    """Get plan for Multio Output

    Parameters
    ----------
    plan : PLANS
        Plan ID to get
    kwargs : dict
        Additional parameters for the plan

    Returns
    -------
    Config
        Multio Plan configuration
    """
    return getattr(CONFIGURED_PLANS, plan)(**kwargs)
