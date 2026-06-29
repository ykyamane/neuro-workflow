from typing import Dict, Any

import numpy as np
import nest

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


class NESTKernelNode(Node):
    """Resets and seeds the global NEST kernel once, before any network is built.

    Both Pong player networks must be created inside a single, freshly reset
    kernel and then simulated together. Because NEST's kernel is global state, a
    reset performed inside an individual network node would wipe out neurons
    created by a sibling node. This node centralises that reset so it happens
    exactly once, and emits a `kernel_ready` flag that downstream network nodes
    consume purely to enforce execution order (kernel first, then players).
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="nest_pong_kernel",
        stage="simulation",
        tool="NEST",
        model_source="https://nest-simulator.readthedocs.io/en/stable/auto_examples/pong/index.html",
        description="Resets and seeds the global NEST simulation kernel (resolution and RNG seed) so all downstream NEST nodes build into one clean, reproducible kernel.",
        parameters={
            "resolution_ms": ParameterDefinition(
                default_value=0.1,
                description="NEST simulation time resolution in milliseconds; must be 0.1 so input spike-train timings (rounded to 0.1 ms) align with the grid.",
                constraints={"min": 0.01, "max": 1.0},
            ),
            "random_seed": ParameterDefinition(
                default_value=1,
                description="Master seed applied to both the NEST RNG and NumPy, making weight initialisation and game randomness reproducible.",
                constraints={"min": 1},
            ),
            "reset_kernel": ParameterDefinition(
                default_value=True,
                description="If True, call nest.ResetKernel() before configuring it. Keep True so re-running the workflow in one Python session starts from a clean kernel.",
            ),
        },
        inputs={},
        outputs={
            "kernel_ready": PortDefinition(
                type=PortType.BOOL,
                description="True once the kernel has been reset and seeded; consumed by network nodes only to order them after this node.",
            ),
        },
        methods={
            "setup": MethodDefinition(
                description="Reset the NEST kernel and set its resolution and RNG seed.",
                inputs=[],
                outputs=["kernel_ready"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("setup", self.setup, method_key="setup")

    def setup(self) -> Dict[str, Any]:
        resolution = float(self._parameters["resolution_ms"])
        seed = int(self._parameters["random_seed"])

        if self._parameters["reset_kernel"]:
            nest.ResetKernel()

        try:
            nest.set_verbosity("M_WARNING")
        except Exception:
            pass

        nest.SetKernelStatus({"resolution": resolution, "rng_seed": seed})
        np.random.seed(seed)

        return {"kernel_ready": True}
