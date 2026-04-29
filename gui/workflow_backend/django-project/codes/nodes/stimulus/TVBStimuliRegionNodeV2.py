from typing import Dict, Any

import numpy as np

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType

from tvb.simulator.lab import patterns, equations, plot_pattern


class TVBStimuliRegionNodeV2(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="tvb_stimuli_region",
        stage="stimulus",
        tool="TVB",
        model_source="https://github.com/the-virtual-brain/tvb-root",
        description=(
            "Builds a TVB StimuliRegion object that delivers spatially weighted, "
            "temporally shaped external input to selected brain regions during simulation, "
            "supporting Gaussian, Sinusoid, and PulseTrain temporal profiles."
        ),
        parameters={
            "region_indices": ParameterDefinition(
                default_value=[0, 7, 13, 33, 42],
                description=(
                    "List of zero-based region indices to stimulate. Each index corresponds to "
                    "a row/column in the connectivity matrix (e.g. [0, 7, 13] for three regions)."
                ),
            ),
            "weights": ParameterDefinition(
                default_value=[0.25, 0.125, 0.0625, 0.03125, 0.015625],
                description=(
                    "Stimulus amplitude weight for each region in region_indices. "
                    "Must have the same length as region_indices. "
                    "Example: [2**-2, 2**-3, 2**-4] for a decreasing gradient."
                ),
            ),
            "temporal_equation": ParameterDefinition(
                default_value="Gaussian",
                description=(
                    "Temporal profile of the stimulus waveform: 'Gaussian' (single pulse, "
                    "defined by midpoint and sigma), 'Sinusoid' (oscillatory, defined by "
                    "frequency), 'PulseTrain' (periodic rectangular pulses)."
                ),
                constraints={"allowed_values": ["Gaussian", "Sinusoid", "PulseTrain"]},
            ),
            "equation_params": ParameterDefinition(
                default_value={"midpoint": 4000.0, "sigma": 200.0},
                description=(
                    "Parameters for the temporal equation. "
                    "Gaussian: {'midpoint': 4000.0, 'sigma': 200.0} (ms). "
                    "Sinusoid: {'frequency': 0.01} (kHz, so 10 Hz). "
                    "PulseTrain: {'T': 100.0, 'tau': 10.0, 'amp': 1.0, 'onset': 500.0}."
                ),
            ),
            "simulation_length": ParameterDefinition(
                default_value=10000.0,
                description=(
                    "Simulation duration in milliseconds; sets the time axis for the "
                    "stimulus pattern plot. Should match the simulator's simulation_length."
                ),
                constraints={"min": 100.0, "max": 1e7},
            ),
        },
        inputs={
            "tvb_connectivity": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB Connectivity object used to determine total number of brain "
                    "regions and build the full spatial weight vector."
                ),
            ),
        },
        outputs={
            "tvb_stimulus": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB StimuliRegion object with spatial weights and temporal "
                    "profile, ready to be passed to the TVB Simulator as external input."
                ),
            ),
            "visualization_completed": PortDefinition(
                type=PortType.BOOL,
                description=(
                    "True once the 3-panel stimulus pattern figure (space, temporal profile, "
                    "space×time heatmap) has been rendered."
                ),
            ),
        },
        methods={
            "build_stimulus": MethodDefinition(
                description=(
                    "Construct a TVB StimuliRegion by mapping region_indices and weights onto "
                    "the full connectivity space and applying the selected temporal equation."
                ),
                inputs=["tvb_connectivity"],
                outputs=["tvb_stimulus"],
            ),
            "plot_stimulus_pattern": MethodDefinition(
                description=(
                    "Visualize the stimulus as a 3-panel plot: spatial weights (which regions), "
                    "temporal waveform (when), and space×time heatmap — using TVB's plot_pattern."
                ),
                inputs=["tvb_stimulus"],
                outputs=["visualization_completed"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step(
            "build_stimulus", self.build_stimulus, method_key="build_stimulus"
        )
        self.add_process_step(
            "plot_stimulus_pattern", self.plot_stimulus_pattern, method_key="plot_stimulus_pattern"
        )

    def build_stimulus(self, tvb_connectivity) -> Dict[str, Any]:
        region_indices = self._parameters["region_indices"]
        weights_vals = self._parameters["weights"]
        temporal_equation = self._parameters["temporal_equation"]
        eq_params = self._parameters["equation_params"]

        if len(region_indices) != len(weights_vals):
            raise ValueError(
                f"region_indices (len {len(region_indices)}) and weights "
                f"(len {len(weights_vals)}) must have the same length."
            )

        nregions = tvb_connectivity.number_of_regions
        weighting = np.zeros(nregions)
        for idx, w in zip(region_indices, weights_vals):
            weighting[idx] = w

        eqn_t = self._build_temporal_equation(temporal_equation, eq_params)

        stim = patterns.StimuliRegion(
            temporal=eqn_t,
            connectivity=tvb_connectivity,
            weight=weighting,
        )

        return {"tvb_stimulus": stim}

    def plot_stimulus_pattern(self, tvb_stimulus) -> Dict[str, Any]:
        simulation_length = self._parameters["simulation_length"]
        tvb_stimulus.configure_space()
        tvb_stimulus.configure_time(np.arange(0.0, simulation_length))
        plot_pattern(tvb_stimulus)
        return {"visualization_completed": True}

    @staticmethod
    def _build_temporal_equation(eq_type: str, params: dict):
        if eq_type == "Gaussian":
            eqn = equations.Gaussian()
            eqn.parameters["midpoint"] = params.get("midpoint", 4000.0)
            eqn.parameters["sigma"] = params.get("sigma", 200.0)
        elif eq_type == "Sinusoid":
            eqn = equations.Sinusoid()
            eqn.parameters["frequency"] = params.get("frequency", 0.01)
        elif eq_type == "PulseTrain":
            eqn = equations.PulseTrain()
            for k, v in params.items():
                eqn.parameters[k] = v
        else:
            raise ValueError(f"Unknown temporal_equation: '{eq_type}'")
        return eqn
