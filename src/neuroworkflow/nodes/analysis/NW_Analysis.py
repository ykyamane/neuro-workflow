from typing import Dict, Any

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition,
)
from neuroworkflow.core.port import PortType


class NW_Analysis(Node):
    """
    Generic BMTK analysis and visualization node — spike raster and membrane traces.

    Tutorial reference: Ch2 Single Cell —
        from bmtk.analyzer.spike_trains import plot_raster, to_dataframe
        from bmtk.analyzer.compartment import plot_traces
        _ = plot_raster(config_file='config.iclamp.json', with_histogram=False)
        _ = plot_traces(config_file='config.iclamp.json', report_name='v_report')

    Scaling path: same node works for single cell, multi-population, any simulator —
    the config JSON already knows which cells were recorded.
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="nw_analysis",
        stage="analysis",
        tool="BMTK",
        model_source="https://alleninstitute.github.io/bmtk/",
        description=(
            "Reads BMTK simulation output and produces spike raster plots and "
            "membrane potential traces using bmtk.analyzer. Works with any BMTK "
            "simulator (PointNet or BioNet) and any number of populations."
        ),
        parameters={
            "plot_raster": ParameterDefinition(
                default_value=True,
                description="Generate a spike raster plot from the output spikes file.",
            ),
            "with_histogram": ParameterDefinition(
                default_value=False,
                description="Add a firing-rate histogram panel below the raster plot.",
            ),
            "plot_traces": ParameterDefinition(
                default_value=True,
                description=(
                    "Generate membrane potential traces. "
                    "Requires a membrane_report entry in NW_SimConfig.reports."
                ),
            ),
            "report_name": ParameterDefinition(
                default_value="v_report",
                description=(
                    "Name of the compartment report to plot (as set in NW_SimConfig.reports). "
                    "Default 'v_report' matches the tutorial."
                ),
            ),
            "populations": ParameterDefinition(
                default_value=[],
                description=(
                    "Population names to analyze. Empty list = auto-detect all populations "
                    "from the spikes file and plot each one. "
                    "Example: ['popA', 'popB'] to restrict to specific populations."
                ),
            ),
            "trace_node_ids": ParameterDefinition(
                default_value=[],
                description=(
                    "Node IDs to plot as individual traces. "
                    "Empty list = all recorded neurons. "
                    "Example: [0, 1, 2] plots three specific neurons."
                ),
            ),
            "save_figures": ParameterDefinition(
                default_value=True,
                description="Save figure PNG files to results_path instead of only displaying.",
            ),
        },
        inputs={
            "results": PortDefinition(
                type=PortType.DICT,
                description=(
                    "Dict from NW_SimConfig with: config_file (str), "
                    "output_dir (str), simulator (str)."
                ),
            ),
        },
        outputs={
            "figures": PortDefinition(
                type=PortType.DICT,
                description=(
                    "Dict with keys 'raster' and 'traces', each containing "
                    "the path to the saved PNG file (or None if disabled)."
                ),
            ),
        },
        methods={
            "analyze": MethodDefinition(
                description=(
                    "Load simulation results and produce spike raster and/or "
                    "membrane potential trace plots."
                ),
                inputs=["results"],
                outputs=["figures"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("analyze", self.analyze, method_key="analyze")

    def _detect_populations(self, output_dir: str, report_name: str) -> list:
        """Detect population names from spikes.h5, falling back to the membrane report."""
        import os
        import h5py

        spikes_path = os.path.join(output_dir, "spikes.h5")
        if os.path.exists(spikes_path):
            with h5py.File(spikes_path, "r") as f:
                pops = list(f.get("spikes", {}).keys())
            if pops:
                return pops

        # No spikes (or silent network) — read populations from the membrane report
        report_path = os.path.join(output_dir, f"{report_name}.h5")
        if os.path.exists(report_path):
            with h5py.File(report_path, "r") as f:
                return list(f.get("report", {}).keys())

        return []

    def analyze(self, results: Dict) -> Dict[str, Any]:
        import os
        import matplotlib.pyplot as plt

        config_file = results["config_file"]
        output_dir  = results["output_dir"]
        p = self._parameters

        populations = list(p["populations"]) or self._detect_populations(output_dir, str(p["report_name"]))
        node_ids    = list(p["trace_node_ids"]) or None
        figures: Dict[str, Any] = {"raster": None, "traces": None}

        if bool(p["plot_raster"]):
            try:
                from bmtk.analyzer.spike_trains import plot_raster
                raster_paths = []
                for pop in populations:
                    plot_raster(
                        config_file    = config_file,
                        population     = pop,
                        with_histogram = bool(p["with_histogram"]),
                        show           = False,
                    )
                    plt.title(pop)
                    if bool(p["save_figures"]):
                        path = os.path.join(output_dir, f"raster_{pop}.png")
                        plt.savefig(path, bbox_inches="tight")
                        raster_paths.append(path)
                    plt.show()
                figures["raster"] = raster_paths or None
            except Exception as e:
                print(f"[NW_Analysis] plot_raster skipped: {e}")

        if bool(p["plot_traces"]):
            try:
                from bmtk.analyzer.compartment import plot_traces
                trace_paths = []
                for pop in populations:
                    plot_traces(
                        config_file = config_file,
                        report_name = str(p["report_name"]),
                        population  = pop,
                        node_ids    = node_ids,
                        show        = False,
                    )
                    plt.title(pop)
                    if bool(p["save_figures"]):
                        path = os.path.join(output_dir, f"traces_{pop}.png")
                        plt.savefig(path, bbox_inches="tight")
                        trace_paths.append(path)
                    plt.show()
                figures["traces"] = trace_paths or None
            except Exception as e:
                print(f"[NW_Analysis] plot_traces skipped: {e}")

        return {"figures": figures}
