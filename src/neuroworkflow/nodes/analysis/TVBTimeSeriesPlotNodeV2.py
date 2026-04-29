from typing import Dict, Any
import os

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


class TVBTimeSeriesPlotNodeV2(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="tvb_timeseries_plot",
        stage="analysis",
        tool="TVB",
        model_source="https://github.com/the-virtual-brain/tvb-root",
        description=(
            "Visualizes TVB simulation output as normalized time series traces for a "
            "selected number of brain regions, compatible with any TVB model and monitor type "
            "(Raw, TemporalAverage, Bold)."
        ),
        parameters={
            "n_regions": ParameterDefinition(
                default_value=10,
                description=(
                    "Number of brain regions to include in the plot, taken from the first "
                    "n_regions entries of the connectivity region labels."
                ),
                constraints={"min": 1, "max": 500},
            ),
            "state_variable_index": ParameterDefinition(
                default_value=0,
                description=(
                    "Index of the state variable to plot from the data array dimension 1 "
                    "(n_state_vars). Use 0 for V in Generic2dOscillator; 0 for x1 in Epileptor."
                ),
                constraints={"min": 0, "max": 20},
            ),
            "normalize": ParameterDefinition(
                default_value=True,
                description=(
                    "If True, normalize each region's time series by its range "
                    "(max - min) so all traces share a comparable amplitude scale."
                ),
            ),
            "title": ParameterDefinition(
                default_value="TVB Simulated Neural Activity",
                description="Title string displayed on the plot.",
            ),
            "save_to_file": ParameterDefinition(
                default_value=False,
                description=(
                    "If True, save the full simulation data (all regions) to a NumPy .npz "
                    "file at output_path, containing arrays 'time' (ms) and 'data' "
                    "(n_timepoints × n_all_regions for the selected state variable)."
                ),
            ),
            "output_path": ParameterDefinition(
                default_value="./simulation_output.npz",
                description=(
                    "File path for the saved .npz file. Used only when save_to_file=True. "
                    "Example: '/results/bold_sim2.npz'."
                ),
            ),
        },
        inputs={
            "tvb_simdata": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Numpy array of simulated data from a TVB monitor, shape "
                    "(n_timepoints, n_state_vars, n_regions, n_modes) or pre-squeezed "
                    "(n_timepoints, n_regions)."
                ),
            ),
            "tvb_simtime": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Numpy array of simulation time points in milliseconds, shape (n_timepoints,)."
                ),
            ),
            "tvb_connectivity": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB Connectivity object used to label the y-axis with brain "
                    "region names."
                ),
                optional=True,
            ),
        },
        outputs={
            "visualization_completed": PortDefinition(
                type=PortType.BOOL,
                description=(
                    "True once the time series figure has been rendered and displayed."
                ),
            ),
            "saved_file_path": PortDefinition(
                type=PortType.STR,
                description=(
                    "Absolute path to the saved .npz file when save_to_file=True; "
                    "None otherwise."
                ),
            ),
        },
        methods={
            "plot_timeseries": MethodDefinition(
                description=(
                    "Squeeze the simulation data array, select the specified state variable, "
                    "optionally normalize by range, plot n_regions traces as offset time series, "
                    "and optionally save the full data to a .npz file (time + data arrays)."
                ),
                inputs=["tvb_simdata", "tvb_simtime", "tvb_connectivity"],
                outputs=["visualization_completed", "saved_file_path"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step(
            "plot_timeseries", self.plot_timeseries, method_key="plot_timeseries"
        )

    def plot_timeseries(
        self,
        tvb_simdata,
        tvb_simtime,
        tvb_connectivity=None,
    ) -> Dict[str, Any]:
        n_regions = self._parameters["n_regions"]
        sv_idx = self._parameters["state_variable_index"]
        normalize = self._parameters["normalize"]
        title = self._parameters["title"]
        save_to_file = self._parameters["save_to_file"]
        output_path = self._parameters["output_path"]

        data = np.array(tvb_simdata)
        time = np.array(tvb_simtime)

        # Handle (n_t, n_sv, n_regions, n_modes) or already squeezed (n_t, n_regions)
        if data.ndim == 4:
            data = data[:, sv_idx, :, 0]
        elif data.ndim == 3:
            data = data[:, sv_idx, :]

        # Save full data (all regions) before slicing for plot
        saved_path = None
        if save_to_file:
            output_path = os.path.abspath(output_path)
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            np.savez(output_path, time=time, data=data)
            saved_path = output_path
            print(f"[{self.name}] Saved simulation data to: {saved_path}")

        n_plot = min(n_regions, data.shape[1])
        plot_data = data[:, :n_plot]

        if normalize:
            rng = np.max(plot_data, axis=0) - np.min(plot_data, axis=0)
            rng[rng == 0] = 1.0
            plot_data = plot_data / rng

        region_labels = None
        if tvb_connectivity is not None:
            region_labels = tvb_connectivity.region_labels[:n_plot]

        fig, ax = plt.subplots(figsize=(12, 8))
        for i in range(n_plot):
            ax.plot(time, plot_data[:, i] + i, color="k", alpha=0.6, linewidth=0.8)

        ax.set_title(title, fontsize=16)
        ax.set_xlabel("Time [ms]", fontsize=13)

        if region_labels is not None:
            ax.set_yticks(range(n_plot))
            ax.set_yticklabels(region_labels, fontsize=9)
        else:
            ax.set_ylabel("Region index (offset)", fontsize=13)

        plt.tight_layout()
        plt.show()

        return {"visualization_completed": True, "saved_file_path": saved_path}
