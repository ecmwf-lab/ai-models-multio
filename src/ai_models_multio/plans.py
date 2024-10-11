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

from multio.plans import Client
from multio.plans import Plan
from multio.plans import actions
from multio.plans import sinks

PLANS = Literal["to_file", "to_fdb", "debug"]

if TYPE_CHECKING:
    import numpy as np
    from earthkit.data.core.metadata import Metadata

LOG = logging.getLogger(__name__)


class CONFIGURED_PLANS:
    """Configured plans for Multio Output"""

    @staticmethod
    def to_file(path: os.PathLike, template_path: os.PathLike, **_) -> Client:
        return Plan(
            actions=[
                actions.Encode(
                    template=str(template_path),
                    format="grib",
                    addtional_metadata={"class": "ml"},
                ),
                actions.Sink(
                    sinks=[
                        sinks.File(
                            path=path,
                            append=True,
                            per_server=False,
                        )
                    ]
                ),
            ],
            name="output-to-file",
        ).to_client()

    @staticmethod
    def to_fdb(path: os.PathLike, template_path: os.PathLike, **_) -> Client:

        try:
            import yaml

            yaml.safe_load(open(path))
        except (FileNotFoundError, ValueError):
            LOG.warning(
                f"'path' should point to an FDB config file.\nFailed to load FDB config from {path!r}, see {str(Path(__file__).parent.absolute()/'fdb'/'example_config.yaml')} for an example."
            )

        return Plan(
            actions=[
                actions.Encode(
                    template=str(template_path),
                    format="grib",
                    addtional_metadata={"class": "ml"},
                ),
                actions.Sink(sinks=[sinks.FDB(config=str(path))]),
            ],
            name="output-to-fdb",
        ).to_client()

    @staticmethod
    def debug(template_path: os.PathLike, **_) -> Client:
        return Plan(
            actions=[
                actions.Print(stream="cout", prefix=" ++ MULTIO-DEBUG-PRIOR-ENCODE :: "),
                actions.Encode(
                    template=str(template_path),
                    format="grib",
                ),
                actions.Print(stream="cout", prefix=" ++ MULTIO-DEBUG-POST-ENCODE :: "),
            ],
            name="debug",
        ).to_client()


def get_encode_params(values: np.ndarray, metadata: Metadata) -> dict:
    """Get path to the template file

    Uses earthkit.data.readers.grib.output.GribCoder to determine the template file

    Pulls from in order:
        - ai_models_multio/templates
        - $MULTIO_RAPS_TEMPLATES_PATH
        - $ECCODES_DIR/share/eccodes/samples
        and fails over to the default template

    Returns
    -------
    dict
        Kwargs for encoding
    """
    metadata = dict(metadata).copy()

    levtype = metadata.get("levtype", None)
    if levtype is None:
        if "levelist" in metadata:
            levtype = "pl"
        else:
            levtype = "sfc"

    edition = metadata.get("edition", 2)

    if len(values.shape) == 1:
        template_name = f"regular_gg_{levtype}_grib{edition}"
    elif len(values.shape) == 2:
        template_name = f"regular_ll_{levtype}_grib{edition}"
    else:
        warnings.warn(
            f"Invalid shape {values.shape} for GRIB, must be 1 or 2 dimension ",
            RuntimeWarning,
        )
        template_name = "default"

    template_path = (Path(__file__).parent / "templates" / (template_name + ".tmpl")).absolute()

    if not template_path.exists():
        if "MULTIO_RAPS_TEMPLATES_PATH" in os.environ:
            template_path = Path(os.environ["MULTIO_RAPS_TEMPLATES_PATH"]) / (template_name + ".tmpl")

        elif "ECCODES_DIR" in os.environ:
            template_path = (
                Path(os.environ["ECCODES_DIR"]) / "share" / "eccodes" / "samples" / (template_name + ".tmpl")
            )
        else:
            warnings.warn(
                f"Template {template_path} does not exist, using default template",
                RuntimeWarning,
            )
            template_path = Path(__file__).parent / "templates" / "default.tmpl"

    LOG.info(f"Using template {str(template_path)!r}")

    return dict(template_path=(template_path.absolute()))


def get_plan(plan: PLANS, values: np.ndarray, metadata: Metadata, **kwargs) -> Client:
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
    Client
        Multio Plan configuration
    """
    encoding_params = get_encode_params(values, metadata)
    return getattr(CONFIGURED_PLANS, plan)(**encoding_params, **kwargs)
