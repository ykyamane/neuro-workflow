from typing import Dict, Any

import numpy as np

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType

from tvb.simulator.lab import monitors


class TVBMonitorNodeV2(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="tvb_monitor",
        stage="simulation",
        tool="TVB",
        model_source="https://github.com/the-virtual-brain/tvb-root",
        description=(
            "Configures a single TVB recording monitor (Raw, TemporalAverage, or Bold) that "
            "observes simulated neural activity at a specified sampling period; one node "
            "per monitor, connect multiple to the simulator for multi-modal recording."
        ),
        parameters={
            "monitor_type": ParameterDefinition(
                default_value="TemporalAverage",
                description=(
                    "TVB monitor class: 'Raw' (all timesteps at dt resolution, large output), "
                    "'TemporalAverage' (time-windowed average at given period, e.g. 10 ms → 100 Hz), "
                    "'Bold' (simulated BOLD fMRI signal via hemodynamic response, period ~500 ms)."
                ),
                constraints={"allowed_values": ["Raw", "TemporalAverage", "Bold"]},
            ),
            "period": ParameterDefinition(
                default_value=10.0,
                description=(
                    "Sampling period in milliseconds for TemporalAverage and Bold monitors. "
                    "TemporalAverage: 10 ms → 100 Hz effective sampling rate. "
                    "Bold: 500–2000 ms typical (matched to TR). Ignored by Raw monitor."
                ),
                constraints={"min": 0.1, "max": 10000.0},
            ),
        },
        inputs={},
        outputs={
            "tvb_monitor": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB monitor object (Raw, TemporalAverage, or Bold) ready to be "
                    "passed to the TVB Simulator as a recording observer."
                ),
            ),
        },
        methods={
            "build_monitor": MethodDefinition(
                description=(
                    "Instantiate the selected TVB monitor class with the given sampling period."
                ),
                inputs=[],
                outputs=["tvb_monitor"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("build_monitor", self.build_monitor, method_key="build_monitor")

    def build_monitor(self) -> Dict[str, Any]:
        monitor_type = self._parameters["monitor_type"]
        period = self._parameters["period"]

        if monitor_type == "Raw":
            mon = monitors.Raw()
        elif monitor_type == "TemporalAverage":
            mon = monitors.TemporalAverage(period=period)
        elif monitor_type == "Bold":
            mon = monitors.Bold(period=period)
        else:
            raise ValueError(f"Unknown monitor_type: '{monitor_type}'")

        return {"tvb_monitor": mon}
