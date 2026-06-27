from typing import Dict, Any

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition,
)
from neuroworkflow.core.port import PortType


class NW_IClamp(Node):
    """
    Somatic current clamp stimulus for BMTK simulations.

    Packages amplitude, delay, and duration into the dict that
    create_environment() expects as its current_clamp argument.
    Connect the output to NW_Population's iclamp port.
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="nw_iclamp",
        stage="stimulus",
        tool="BMTK",
        model_source="https://alleninstitute.github.io/bmtk/",
        description=(
            "Defines a somatic current clamp stimulus. "
            "Output is a dict passed directly to BMTK's create_environment(current_clamp=...). "
            "Connect to NW_Population.iclamp."
        ),
        parameters={
            "amp_na": ParameterDefinition(
                default_value=0.15,
                description="Injected current amplitude in nanoamperes (nA).",
                constraints={"min": -1000.0, "max": 1000.0},
            ),
            "delay_ms": ParameterDefinition(
                default_value=500.0,
                description="Onset delay in milliseconds before current injection begins.",
                constraints={"min": 0.0},
            ),
            "duration_ms": ParameterDefinition(
                default_value=2000.0,
                description="Duration of the current pulse in milliseconds.",
                constraints={"min": 0.0},
            ),
        },
        inputs={},
        outputs={
            "iclamp": PortDefinition(
                type=PortType.DICT,
                description=(
                    "Dict with keys amp, delay, duration. "
                    "Connect to NW_Population.iclamp."
                ),
            ),
        },
        methods={
            "build": MethodDefinition(
                description="Package IClamp parameters into a dict for NW_Population.",
                inputs=[],
                outputs=["iclamp"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("build", self.build, method_key="build")

    def build(self) -> Dict[str, Any]:
        p = self._parameters
        return {
            "iclamp": {
                "amp":      float(p["amp_na"]),
                "delay":    float(p["delay_ms"]),
                "duration": float(p["duration_ms"]),
            }
        }
