from typing import Dict, Any

import numpy as np
import matplotlib.pyplot as plt

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


class SNNbuilder_Raster(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="snnbuilder_raster",
        stage="analysis",
        tool="SNNbuilder",
        model_source="https://github.com/oist/neuro-workflow",
        description=(
            "Reads spike events from a NEST spike recorder, derives population size "
            "and simulation duration from the data, and produces a raster plot and "
            "PSTH (peri-stimulus time histogram) of spiking activity."
        ),
        parameters={
            "bin_size": ParameterDefinition(
                default_value=10.0,
                description="Bin width in ms for the PSTH histogram.",
                constraints={"min": 0.1, "max": 1000.0},
            ),
            "figure_size": ParameterDefinition(
                default_value=[12, 7],
                description="Figure size [width, height] in inches.",
            ),
            "title": ParameterDefinition(
                default_value="",
                description="Optional title for the figure. Left empty if not set.",
            ),
            "save_path": ParameterDefinition(
                default_value="",
                description="File path to save the figure (e.g. 'raster.png'). Skipped if empty.",
            ),
        },
        inputs={
            "nest_recorders": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "NEST NodeCollection of spike_recorder devices whose events "
                    "contain 'senders' (neuron GIDs) and 'times' (spike times in ms)."
                ),
            ),
            "simulation_done": PortDefinition(
                type=PortType.BOOL,
                optional=True,
                description=(
                    "Ordering port — receive any output from SNNbuilder_Simulation to ensure "
                    "this node executes after nest.Simulate() has populated spike events."
                ),
            ),
        },
        outputs={
            "figure": PortDefinition(
                type=PortType.OBJECT,
                description="matplotlib Figure with raster plot (top) and PSTH (bottom).",
            ),
            "spike_stats": PortDefinition(
                type=PortType.DICT,
                description=(
                    "Summary dict with keys: n_neurons (int), sim_time_ms (float), "
                    "total_spikes (int), mean_firing_rate_hz (float)."
                ),
            ),
        },
        methods={
            "extract_spikes": MethodDefinition(
                description="Retrieve spike times and sender IDs from the NEST recorder events.",
                inputs=["nest_recorders", "simulation_done"],
                outputs=[],
            ),
            "generate_plots": MethodDefinition(
                description=(
                    "Build raster plot and PSTH from extracted spike data; compute "
                    "summary statistics. Population size and simulation duration are "
                    "derived directly from the spike events — no manual parameters needed."
                ),
                inputs=[],
                outputs=["figure", "spike_stats"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._spike_times = None
        self._spike_senders = None
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("extract_spikes", self.extract_spikes, method_key="extract_spikes")
        self.add_process_step("generate_plots", self.generate_plots, method_key="generate_plots")

    # ------------------------------------------------------------------
    def extract_spikes(self, nest_recorders, simulation_done=None) -> Dict[str, Any]:
        import nest

        status = nest.GetStatus(nest_recorders)[0]
        events = status.get("events", {})
        self._spike_times   = np.array(events.get("times",   []), dtype=float)
        self._spike_senders = np.array(events.get("senders", []), dtype=int)
        return {}

    # ------------------------------------------------------------------
    def generate_plots(self) -> Dict[str, Any]:
        times   = self._spike_times
        senders = self._spike_senders

        n_neurons = int(np.unique(senders).size) if senders.size > 0 else 1
        sim_time  = float(np.max(times))         if times.size  > 0 else 0.0
        total_spikes = int(times.size)
        mean_fr = (total_spikes / n_neurons / (sim_time / 1000.0)) if sim_time > 0 else 0.0

        bin_size    = float(self._parameters["bin_size"])
        figure_size = self._parameters["figure_size"]
        title       = str(self._parameters["title"])
        save_path   = str(self._parameters["save_path"])

        fig, (ax_raster, ax_psth) = plt.subplots(
            2, 1,
            figsize=figure_size,
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1]},
        )

        if times.size > 0:
            ax_raster.scatter(times, senders, s=1, c="black", linewidths=0)
        ax_raster.set_ylabel("Neuron ID")
        ax_raster.set_title(title or f"Raster plot — {n_neurons} neurons, {sim_time:.0f} ms")

        bins = np.arange(0, sim_time + bin_size, bin_size)
        if times.size > 0:
            ax_psth.hist(times, bins=bins, color="steelblue", edgecolor="none")
        ax_psth.set_xlabel("Time (ms)")
        ax_psth.set_ylabel(f"Spikes / {bin_size:.0f} ms")

        fig.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")

        spike_stats = {
            "n_neurons":            n_neurons,
            "sim_time_ms":          sim_time,
            "total_spikes":         total_spikes,
            "mean_firing_rate_hz":  round(mean_fr, 3),
        }
        return {"figure": fig, "spike_stats": spike_stats}
