"""A dependency-free example *source* node.

Generates a deterministic sine wave as a list of float samples. It needs no
simulator and no inputs, so it always runs — the ideal first node for a green
run and a correct pattern for an agent to imitate.
"""

import math
from typing import Dict, Any

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


class SignalGeneratorNode(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="hello_signal_generator",
        stage="stimulus",
        tool="custom",
        model_source="https://github.com/oist/neuro-workflow (hackathon hello example)",
        description="Generate a deterministic sine wave as a list of float samples; a dependency-free source node used as the hackathon green-run example.",
        parameters={
            "length": ParameterDefinition(
                default_value=100,
                description="Number of samples to generate.",
                constraints={"min": 1},
            ),
            "amplitude": ParameterDefinition(
                default_value=1.0,
                description="Peak amplitude of the sine wave (dimensionless).",
            ),
            "cycles": ParameterDefinition(
                default_value=2.0,
                description="Number of full sine cycles spanning the generated signal.",
            ),
        },
        inputs={},
        outputs={
            "signal": PortDefinition(
                type=PortType.LIST,
                description="Sine wave as a list of float samples, length == 'length'.",
            ),
            "n_samples": PortDefinition(
                type=PortType.INT,
                description="Number of samples in the generated signal.",
            ),
        },
        methods={
            "generate": MethodDefinition(
                description="Generate the sine wave signal.",
                inputs=[],
                outputs=["signal", "n_samples"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("generate", self.generate, method_key="generate")

    def generate(self) -> Dict[str, Any]:
        length = int(self._parameters["length"])
        amplitude = float(self._parameters["amplitude"])
        cycles = float(self._parameters["cycles"])
        signal = [
            amplitude * math.sin(2.0 * math.pi * cycles * i / length)
            for i in range(length)
        ]
        # The return-dict keys MUST match the output port names exactly,
        # otherwise the port silently stays None.
        return {"signal": signal, "n_samples": length}
