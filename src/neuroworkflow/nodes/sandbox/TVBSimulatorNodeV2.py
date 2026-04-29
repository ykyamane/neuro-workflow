import time as tm
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

from tvb.simulator.lab import simulator


class TVBSimulatorNodeV2(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="tvb_simulator",
        stage="simulation",
        tool="TVB",
        model_source="https://github.com/the-virtual-brain/tvb-root",
        description=(
            "Assembles and executes a TVB brain network simulation from connectivity, neural mass "
            "model, coupling, integrator, and one or two monitors, with optional region-based "
            "stimulus; returns time and data arrays for each connected monitor."
        ),
        parameters={
            "simulation_length": ParameterDefinition(
                default_value=10000.0,
                description=(
                    "Total simulation duration in milliseconds. "
                    "10000 ms (10 s) for resting-state exploration; "
                    "60000 ms (1 min) for BOLD signal generation."
                ),
                constraints={"min": 100.0, "max": 1e7},
                optimizable=False,
            ),
        },
        inputs={
            "tvb_connectivity": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB Connectivity object (structural connectome with weights, tract "
                    "lengths, and conduction speed) for the brain network."
                ),
            ),
            "tvb_model": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB neural mass model object (e.g. Generic2dOscillator, "
                    "EpileptorRestingState) defining local node dynamics."
                ),
            ),
            "tvb_coupling": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB coupling function object (Scaling, Linear, or Difference) "
                    "that mediates long-range interactions between brain regions."
                ),
            ),
            "tvb_integrator": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB integrator object (HeunDeterministic or HeunStochastic) "
                    "defining the numerical integration scheme and noise."
                ),
            ),
            "tvb_monitor": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Primary TVB monitor object (Raw, TemporalAverage, or Bold) for recording "
                    "simulated neural activity."
                ),
            ),
            "tvb_monitor_2": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Optional secondary TVB monitor for simultaneous dual-modal recording "
                    "(e.g. TemporalAverage as primary + Bold as secondary)."
                ),
                optional=True,
            ),
            "tvb_stimulus": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Optional TVB StimuliRegion object defining spatiotemporal external input "
                    "to selected brain regions during the simulation."
                ),
                optional=True,
            ),
        },
        outputs={
            "tvb_simdata": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Numpy array of simulated data from the primary monitor, shape "
                    "(n_timepoints, n_state_vars, n_regions, n_modes)."
                ),
            ),
            "tvb_simtime": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Numpy array of simulation time points in milliseconds for the primary monitor, "
                    "shape (n_timepoints,)."
                ),
            ),
            "tvb_simdata_2": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Numpy array of simulated data from the secondary monitor (None if tvb_monitor_2 "
                    "not connected), shape (n_timepoints, n_state_vars, n_regions, n_modes)."
                ),
            ),
            "tvb_simtime_2": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Numpy array of time points for the secondary monitor in milliseconds "
                    "(None if tvb_monitor_2 not connected), shape (n_timepoints,)."
                ),
            ),
        },
        methods={
            "run_simulation": MethodDefinition(
                description=(
                    "Assemble the TVB Simulator from all components, configure it, and run for "
                    "simulation_length ms, collecting data from one or two monitors."
                ),
                inputs=[
                    "tvb_connectivity",
                    "tvb_model",
                    "tvb_coupling",
                    "tvb_integrator",
                    "tvb_monitor",
                    "tvb_monitor_2",
                    "tvb_stimulus",
                ],
                outputs=["tvb_simdata", "tvb_simtime", "tvb_simdata_2", "tvb_simtime_2"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step(
            "run_simulation", self.run_simulation, method_key="run_simulation"
        )

    def run_simulation(
        self,
        tvb_connectivity,
        tvb_model,
        tvb_coupling,
        tvb_integrator,
        tvb_monitor,
        tvb_monitor_2=None,
        tvb_stimulus=None,
    ) -> Dict[str, Any]:
        monitor_list = [tvb_monitor]
        if tvb_monitor_2 is not None:
            monitor_list.append(tvb_monitor_2)

        sim_kwargs = dict(
            model=tvb_model,
            connectivity=tvb_connectivity,
            conduction_speed=float(np.asarray(tvb_connectivity.speed).flat[0]),
            coupling=tvb_coupling,
            integrator=tvb_integrator,
            monitors=monitor_list,
        )
        if tvb_stimulus is not None:
            sim_kwargs["stimulus"] = tvb_stimulus

        sim = simulator.Simulator(**sim_kwargs)
        sim.configure()

        n_monitors = len(monitor_list)
        times = [[] for _ in range(n_monitors)]
        data = [[] for _ in range(n_monitors)]

        tic = tm.time()
        for step_output in sim(simulation_length=self._parameters["simulation_length"]):
            for i, mon_out in enumerate(step_output):
                if mon_out is not None:
                    times[i].append(mon_out[0])
                    data[i].append(mon_out[1])
        print(f"[{self.name}] simulation completed in {tm.time() - tic:.3f}s")

        tvb_simtime = np.array(times[0])
        tvb_simdata = np.array(data[0])
        tvb_simtime_2 = np.array(times[1]) if n_monitors > 1 else None
        tvb_simdata_2 = np.array(data[1]) if n_monitors > 1 else None

        return {
            "tvb_simdata": tvb_simdata,
            "tvb_simtime": tvb_simtime,
            "tvb_simdata_2": tvb_simdata_2,
            "tvb_simtime_2": tvb_simtime_2,
        }
