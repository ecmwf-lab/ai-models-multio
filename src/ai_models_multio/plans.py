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

from multio.plans import Config
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
    def to_file(path: os.PathLike, template_path: os.PathLike, atlas_named_grid: str, **_) -> Config:
        return Plan(
            actions=[
                actions.Encode(
                    template=str(template_path),
                    format="grib",
                    atlas_named_grid=atlas_named_grid,
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
        ).to_config()

    @staticmethod
    def to_fdb(path: os.PathLike, template_path: os.PathLike, atlas_named_grid: str, **_) -> Config:

        try:
            import yaml

            yaml.safe_load(open(path))
        except ValueError:
            LOG.warning(
                f"Failed to load FDB config from {path!r}, see {str(Path(__file__).parent.absolute()/'fdb'/'example_config.yaml')} for an example."
            )

        return Plan(
            actions=[
                actions.Encode(
                    template=str(template_path),
                    format="grib",
                    atlas_named_grid=atlas_named_grid,
                    addtional_metadata={"class": "ml"},
                ),
                actions.Sink(sinks=[sinks.FDB(config=str(path))]),
            ],
            name="output-to-fdb",
        ).to_config()

    @staticmethod
    def debug(template_path: os.PathLike, atlas_named_grid: str, **_) -> Config:
        return Plan(
            actions=[
                actions.Print(stream="cout", prefix=" ++ MULTIO-DEBUG-PRIOR-ENCODE :: "),
                actions.Encode(
                    template=str(template_path),
                    format="grib",
                    atlas_named_grid=atlas_named_grid,
                ),
                actions.Print(stream="cout", prefix=" ++ MULTIO-DEBUG-POST-ENCODE :: "),
            ],
            name="debug",
        ).to_config()


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
    # from earthkit.data.readers.grib.output import GribCoder

    # coder = GribCoder()
    metadata = dict(metadata).copy()

    # metadata["edition"] = metadata.get("gribEdition", 2)
    # metadata["levtype"] = 'pl'

    levtype = metadata.get("levtype", None)
    if levtype is None:
        if "levelist" in metadata:
            levtype = "pl"
        else:
            levtype = "sfc"

    edition = metadata.get("edition", 2)

    if len(values.shape) == 1:
        template_name = f"regular_gg_{levtype}_grib{edition}"
        raise NotImplementedError("Grid type GAUSSIAN not implemented")
        # template_name = coder._gg_field(values, metadata)
    elif len(values.shape) == 2:
        template_name = f"regular_ll_{levtype}_grib{edition}"
        Nj, Ni = values.shape
        # template_name = coder._ll_field(values, metadata)
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

    grid_type = f"L{Ni}x{Nj}"

    LOG.info(f"Using template {str(template_path)!r}")
    LOG.info(f"Using {grid_type=!r}")

    return dict(template_path=(template_path.absolute()), atlas_named_grid=grid_type)


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
    encoding_params = get_encode_params(values, metadata)
    return getattr(CONFIGURED_PLANS, plan)(**encoding_params, **kwargs)
