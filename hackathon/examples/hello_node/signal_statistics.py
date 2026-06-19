"""A dependency-free example *analysis* node.

Consumes a list of float samples and reports summary statistics. Pairs with
SignalGeneratorNode to form a minimal two-node workflow.
"""

import statistics as stats
from typing import Dict, Any

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


class SignalStatisticsNode(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="hello_signal_statistics",
        stage="analysis",
        tool="custom",
        model_source="https://github.com/oist/neuro-workflow (hackathon hello example)",
        description="Compute summary statistics (mean, population standard deviation, sample count) of a list of float samples.",
        parameters={},
        inputs={
            "signal": PortDefinition(
                type=PortType.LIST,
                description="List of float samples to summarize.",
            ),
        },
        outputs={
            "mean": PortDefinition(
                type=PortType.FLOAT,
                description="Arithmetic mean of the input samples.",
            ),
            "std": PortDefinition(
                type=PortType.FLOAT,
                description="Population standard deviation of the input samples.",
            ),
            "n_samples": PortDefinition(
                type=PortType.INT,
                description="Number of samples summarized.",
            ),
        },
        methods={
            "compute": MethodDefinition(
                description="Compute mean, population standard deviation, and sample count.",
                inputs=["signal"],
                outputs=["mean", "std", "n_samples"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("compute", self.compute, method_key="compute")

    def compute(self, signal) -> Dict[str, Any]:
        values = [float(v) for v in signal]
        return {
            "mean": stats.fmean(values),
            "std": stats.pstdev(values),
            "n_samples": len(values),
        }
