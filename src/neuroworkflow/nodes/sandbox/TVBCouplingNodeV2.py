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

from tvb.simulator.lab import coupling


class TVBCouplingNodeV2(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="tvb_coupling",
        stage="connectivity",
        tool="TVB",
        model_source="https://github.com/the-virtual-brain/tvb-root",
        description=(
            "Configures a TVB long-range coupling function (Scaling, Linear, or Difference) "
            "that modulates how pre-synaptic activity from structurally connected brain regions "
            "drives local node dynamics in a TVB network simulation."
        ),
        parameters={
            "coupling_type": ParameterDefinition(
                default_value="Scaling",
                description=(
                    "TVB coupling class: 'Scaling' (constant multiplication of incoming activity, "
                    "used with Generic2dOscillator resting-state), 'Linear' (linear slope + intercept), "
                    "'Difference' (difference of pre- and post-synaptic states, used with "
                    "EpileptorRestingState/Epileptor)."
                ),
                constraints={"allowed_values": ["Scaling", "Linear", "Difference"]},
            ),
            "a": ParameterDefinition(
                default_value=0.0075,
                description=(
                    "Global coupling strength parameter (scale factor G). "
                    "Typical range for Scaling with Generic2dOscillator resting-state: 0.001–0.05. "
                    "For Difference with EpileptorRestingState: ~1.0."
                ),
                constraints={"min": 0.0, "max": 10.0},
                optimizable=True,
                optimization_range=[0.001, 0.1],
            ),
            "b": ParameterDefinition(
                default_value=0.0,
                description=(
                    "Intercept for Linear coupling only; additive offset after slope multiplication. "
                    "Ignored by Scaling and Difference coupling types."
                ),
                constraints={"min": -10.0, "max": 10.0},
            ),
        },
        inputs={},
        outputs={
            "tvb_coupling": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB coupling function object that mediates long-range interactions "
                    "between brain regions; passed directly to the TVB Simulator."
                ),
            ),
        },
        methods={
            "build_coupling": MethodDefinition(
                description=(
                    "Instantiate the selected TVB coupling class with parameters a (and b for Linear), "
                    "returning a configured coupling object."
                ),
                inputs=[],
                outputs=["tvb_coupling"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("build_coupling", self.build_coupling, method_key="build_coupling")

    def build_coupling(self) -> Dict[str, Any]:
        coupling_type = self._parameters["coupling_type"]
        a = np.array([self._parameters["a"]])
        b = np.array([self._parameters["b"]])

        if coupling_type == "Scaling":
            con_coupling = coupling.Scaling(a=a)
        elif coupling_type == "Linear":
            con_coupling = coupling.Linear(a=a, b=b)
        elif coupling_type == "Difference":
            con_coupling = coupling.Difference(a=a)
        else:
            raise ValueError(f"Unknown coupling_type: '{coupling_type}'")

        return {"tvb_coupling": con_coupling}
