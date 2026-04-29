import time
from typing import Dict, Any

import nest

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType

from neuroworkflow.utils.BG.BG_helpers import read_spikes


class NESTBGSimulationNode(Node):
    """Run a NEST BG simulation and compute firing rates.

    Currently implements **resting state**: no external stimulus, purely
    endogenous activity driven by the DC currents set in bg_params.

    Other modalities (action selection, plasticity) can be added here as
    additional process steps or a `mode` parameter in a future version.
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="nest_bg_simulation",
        stage="simulation",
        tool="NEST",
        model_source="Girard et al. — top_BG_nest3",
        description=(
            "Execute a NEST 3 Basal Ganglia simulation.  In resting-state mode the network "
            "runs for sim_duration_ms with no external stimulation; spontaneous activity is "
            "driven entirely by the DC currents configured in NESTBGParametersNode.  "
            "Returns mean and instantaneous firing rates per nucleus."
        ),
        parameters={
            "mode": ParameterDefinition(
                default_value="resting_state",
                description=(
                    "Simulation modality.  Currently only 'resting_state' is implemented. "
                    "Future values: 'action_selection', 'plasticity'."
                ),
            ),
        },
        inputs={
            "bg_layers": PortDefinition(
                type=PortType.OBJECT,
                description="Live NEST NodeCollection dict from NESTBGNetworkNode.",
            ),
            "spike_detectors": PortDefinition(
                type=PortType.OBJECT,
                description="NEST spike recorder dict from NESTBGNetworkNode.",
            ),
            "sim_params": PortDefinition(
                type=PortType.OBJECT,
                description="Simulation control dict from NESTBGParametersNode.",
            ),
        },
        outputs={
            "mean_fr": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Dict mapping nucleus → mean firing rate in Hz, computed over "
                    "the period [warmup_ms, sim_duration_ms]."
                ),
            ),
            "at_fr": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Dict mapping nucleus → list of 1-ms-binned instantaneous firing "
                    "rates (Hz) over the recording window."
                ),
            ),
            "sim_params": PortDefinition(
                type=PortType.OBJECT,
                description="Sim params passed through for use by NESTBGWriterNode.",
            ),
        },
        methods={
            "run_resting_state": MethodDefinition(
                description=(
                    "Call nest.Simulate(sim_duration_ms), then compute mean and "
                    "instantaneous firing rates from the spike recorders."
                ),
                inputs=["bg_layers", "spike_detectors", "sim_params"],
                outputs=["mean_fr", "at_fr", "sim_params"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step(
            "run_resting_state", self.run_resting_state, method_key="run_resting_state"
        )

    def run_resting_state(
        self,
        bg_layers: dict,
        spike_detectors: dict,
        sim_params: dict,
    ) -> Dict[str, Any]:
        mode = self._parameters["mode"]
        if mode != "resting_state":
            raise NotImplementedError(
                f"Mode '{mode}' is not yet implemented.  Only 'resting_state' is supported."
            )

        duration = sim_params["simDuration"] + sim_params["initial_ignore"]
        print(f"[{self.name}] Starting resting-state simulation — {duration} ms ...")
        t0 = time.time()
        nest.Simulate(duration)
        elapsed = time.time() - t0
        print(f"[{self.name}] Simulation finished in {elapsed:.1f} s")

        mean_fr, at_fr = read_spikes(spike_detectors, bg_layers, sim_params)

        print(f"[{self.name}] Mean firing rates (Hz):")
        for nucleus, rate in mean_fr.items():
            print(f"  {nucleus:12s}  {rate:.2f}")

        return {"mean_fr": mean_fr, "at_fr": at_fr, "sim_params": sim_params}
