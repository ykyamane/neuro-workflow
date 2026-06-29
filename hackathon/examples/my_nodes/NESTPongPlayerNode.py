from typing import Dict, Any, Optional

from networks import PongNetRSTDP, PongNetDopa

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


class NESTPongPlayerNode(Node):
    """Builds one spiking-neural-network Pong player in the live NEST kernel.

    A player consists of an input layer (spike generators -> parrot neurons)
    fully connected to a motor/output layer (iaf_psc_exp neurons) whose spike
    counts select a paddle action. Two plasticity rules are supported: reward-
    modulated STDP (`rstdp`) updates static-synapse weights after each step,
    while `dopa` uses an actor-critic network of dopaminergic synapses. This is
    a single configurable node, instantiated once per player (left and right).
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="nest_pong_player",
        stage="network",
        tool="NEST",
        model_source="https://github.com/electronicvisions/model-sw-pong",
        description="Constructs a two-layer spiking Pong player network in NEST using either reward-modulated STDP or dopaminergic actor-critic plasticity, ready to be trained by the match-simulation node.",
        parameters={
            "learning_rule": ParameterDefinition(
                default_value="rstdp",
                description="Plasticity rule: 'rstdp' (reward-modulated STDP on static synapses, PongNetRSTDP) or 'dopa' (dopaminergic actor-critic, PongNetDopa). At most one 'dopa' player may exist per kernel.",
                constraints={"allowed_values": ["rstdp", "dopa"]},
            ),
            "apply_noise": ParameterDefinition(
                default_value=False,
                description="If True, add background Poisson/noise input to the motor neurons (the 'noisy' variant); if False, input-to-motor weights are scaled up to compensate.",
            ),
            "num_neurons": ParameterDefinition(
                default_value=20,
                description="Number of neurons in both the input and motor layer; must match the game grid height (y_grid=20) used by the Pong simulation.",
                constraints={"min": 2, "max": 100},
            ),
            "player_side": ParameterDefinition(
                default_value="left",
                description="Which side of the board this network plays on; used only as a human-readable label.",
                constraints={"allowed_values": ["left", "right"]},
            ),
        },
        inputs={
            "kernel_ready": PortDefinition(
                type=PortType.BOOL,
                description="Flag from the kernel node signalling the NEST kernel has been reset/seeded; used only to order this node after kernel setup.",
                optional=True,
            ),
        },
        outputs={
            "player_network": PortDefinition(
                type=PortType.OBJECT,
                description="Live PongNet instance (PongNetRSTDP or PongNetDopa) with neurons/synapses already created in the current NEST kernel; consumed by the match-simulation node.",
            ),
            "network_label": PortDefinition(
                type=PortType.STR,
                description="Short human-readable description of the network type, e.g. 'clean R-STDP' or 'noisy TD'.",
            ),
        },
        methods={
            "build": MethodDefinition(
                description="Instantiate the selected PongNet subclass in the live NEST kernel.",
                inputs=["kernel_ready"],
                outputs=["player_network", "network_label"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("build", self.build, method_key="build")

    def build(self, kernel_ready: Optional[bool] = None) -> Dict[str, Any]:
        rule = str(self._parameters["learning_rule"])
        apply_noise = bool(self._parameters["apply_noise"])
        num_neurons = int(self._parameters["num_neurons"])

        if rule == "rstdp":
            network = PongNetRSTDP(apply_noise, num_neurons)
        else:
            network = PongNetDopa(apply_noise, num_neurons)

        return {"player_network": network, "network_label": repr(network)}
