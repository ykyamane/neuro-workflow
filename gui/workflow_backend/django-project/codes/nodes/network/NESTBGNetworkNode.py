from typing import Dict, Any

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType

from neuroworkflow.utils.BG.BG_helpers import (
    initialize_nest,
    build_bg_network,
)


class NESTBGNetworkNode(Node):
    """Initialise the NEST kernel and build the full Basal Ganglia network.

    Calls initialize_nest() then build_bg_network(), which creates all 10
    populations (MSN_d1/d2, FSI, STN, GPe, GPi, GPi_fake, CSN, PTN, CMPf),
    wires all 36 projections, and attaches spike recorders to every layer.
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="nest_bg_network",
        stage="setup",
        tool="NEST",
        model_source="Girard et al. — top_BG_nest3",
        description=(
            "Initialise the NEST 3 kernel and instantiate the full Basal Ganglia network "
            "from bg_params and sim_params.  Outputs bg_layers (dict of NodeCollections) "
            "and spike detectors, both kept live in the Jupyter kernel for downstream nodes."
        ),
        parameters={},
        inputs={
            "bg_params": PortDefinition(
                type=PortType.OBJECT,
                description="BG network parameters dict from NESTBGParametersNode.",
            ),
            "sim_params": PortDefinition(
                type=PortType.OBJECT,
                description="Simulation control dict from NESTBGParametersNode.",
            ),
        },
        outputs={
            "bg_layers": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Dict mapping nucleus name → NEST NodeCollection. "
                    "Keys: MSN_d1, MSN_d2, FSI, STN, GPe, GPi, GPi_fake, CSN, PTN, CMPf."
                ),
            ),
            "spike_detectors": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Dict mapping nucleus name → NEST spike_recorder NodeCollection. "
                    "Same keys as bg_layers plus a combined 'MSN' recorder."
                ),
            ),
            "sim_params": PortDefinition(
                type=PortType.OBJECT,
                description="Sim params passed through (unchanged) for use by downstream nodes.",
            ),
        },
        methods={
            "build_network": MethodDefinition(
                description=(
                    "Reset and configure the NEST kernel, then create all populations, "
                    "wire all connections, and attach spike recorders."
                ),
                inputs=["bg_params", "sim_params"],
                outputs=["bg_layers", "spike_detectors", "sim_params"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("build_network", self.build_network, method_key="build_network")

    def build_network(self, bg_params: dict, sim_params: dict) -> Dict[str, Any]:
        print(f"[{self.name}] Initialising NEST kernel...")
        initialize_nest(sim_params)

        print(f"[{self.name}] Building BG network (this may take 1–3 minutes)...")
        bg_layers, spike_detectors = build_bg_network(bg_params, sim_params)

        nuclei = list(bg_layers.keys())
        print(f"[{self.name}] Network ready — populations: {nuclei}")
        return {
            "bg_layers":       bg_layers,
            "spike_detectors": spike_detectors,
            "sim_params":      sim_params,
        }
