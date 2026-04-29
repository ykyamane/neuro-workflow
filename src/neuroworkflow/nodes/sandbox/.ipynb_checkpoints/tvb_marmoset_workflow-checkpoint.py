"""
TVB Marmoset Brain Simulation — single configurable workflow.

Default configuration: Sim 1 (resting state, no stimulus).
To switch simulations, change only the marked parameters:

  Sim 1 → Sim 2: set weights = [0.25, 0.125, 0.0625, 0.03125, 0.015625]
  Sim 2 → Sim 3: set T = 30000.0  (2 pulses instead of ~5)

Output files (./results/):
  temporal_average.npz, bold.npz
"""

import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()

CONNECTIVITY_FILE = os.path.abspath(
    os.path.join(
        _HERE,
        "../../../../temp/models/TVB/TVB_1st_step_marmoset/dataset/connectivity_marmoset.zip",
    )
)

from neuroworkflow import WorkflowBuilder
from neuroworkflow.nodes.network.TVBConnectivitySetUpNode import TVBConnectivitySetUpNode
from neuroworkflow.nodes.sandbox.TVBModelNode import TVBModelNode
from neuroworkflow.nodes.sandbox.TVBCouplingNode import TVBCouplingNode
from neuroworkflow.nodes.sandbox.TVBIntegratorNode import TVBIntegratorNode
from neuroworkflow.nodes.sandbox.TVBMonitorNode import TVBMonitorNode
from neuroworkflow.nodes.sandbox.TVBSimulatorNode import TVBSimulatorNode
from neuroworkflow.nodes.sandbox.TVBStimuliRegionNode import TVBStimuliRegionNode
from neuroworkflow.nodes.sandbox.TVBTimeSeriesPlotNode import TVBTimeSeriesPlotNode

# ── Instantiate nodes ──────────────────────────────────────────────────────────

conn       = TVBConnectivitySetUpNode("Connectivity")
model      = TVBModelNode("Model")
coupling   = TVBCouplingNode("Coupling")
integrator = TVBIntegratorNode("Integrator")
monitor    = TVBMonitorNode("Monitor")        # TemporalAverage
monitor2   = TVBMonitorNode("Monitor2")       # Bold
stimulus   = TVBStimuliRegionNode("Stimulus")
sim        = TVBSimulatorNode("Simulator")
plot       = TVBTimeSeriesPlotNode("Plot")    # TemporalAverage output
plot2      = TVBTimeSeriesPlotNode("Plot2")   # Bold output

# ── Configure nodes ────────────────────────────────────────────────────────────

conn.configure(connectivity_file=CONNECTIVITY_FILE)

model.configure(
    model_type="Generic2dOscillator",
    model_params={"a": 1.74},   # Sim 2/3: change to 0.5
    region_params={},
)
coupling.configure(
    coupling_type="Scaling",    # Sim 2/3: change to "Linear"
    a=0.0075,                   # Sim 2/3: change to 0.0126
)
integrator.configure(
    integrator_type="HeunStochastic",   # Sim 2/3: change to "HeunDeterministic"
    dt=0.5,
    nsig=[0.001, 0.0],                  # Sim 2/3: change to [0.0, 0.0]
)
monitor.configure(
    monitor_type="TemporalAverage",
    period=10.0,                # Sim 2/3: change to 1.0
)
monitor2.configure(
    monitor_type="Bold",
    period=500.0,
)
stimulus.configure(
    region_indices=[0, 7, 13, 33, 42],
    weights=[0.0, 0.0, 0.0, 0.0, 0.0],             # ← Sim 2/3: [0.25, 0.125, 0.0625, 0.03125, 0.015625]
    temporal_equation="PulseTrain",
    equation_params={"T": 10000.0, "tau": 1000.0, "amp": 1.0, "onset": 5000.0},
    #                 ↑ Sim 3: change T to 30000.0
    simulation_length=30000.0,  # Sim 2/3: change to 60000.0
)
sim.configure(simulation_length=30000.0)            # Sim 2/3: change to 60000.0

plot.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="TVB Marmoset — TemporalAverage",
    save_to_file=True, output_path="./results/temporal_average.npz",
)
plot2.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="TVB Marmoset — BOLD",
    save_to_file=True, output_path="./results/bold.npz",
)

# ── Build topology ─────────────────────────────────────────────────────────────

wf = WorkflowBuilder("TVB_Marmoset")

wf.add_node(conn)
wf.add_node(model)
wf.add_node(coupling)
wf.add_node(integrator)
wf.add_node(monitor)
wf.add_node(monitor2)
wf.add_node(stimulus)
wf.add_node(sim)
wf.add_node(plot)
wf.add_node(plot2)

wf.connect("Connectivity", "tvb_connectivity", "Model",      "tvb_connectivity")
wf.connect("Connectivity", "tvb_connectivity", "Simulator",  "tvb_connectivity")
wf.connect("Connectivity", "tvb_connectivity", "Stimulus",   "tvb_connectivity")
wf.connect("Connectivity", "tvb_connectivity", "Plot",       "tvb_connectivity")
wf.connect("Connectivity", "tvb_connectivity", "Plot2",      "tvb_connectivity")
wf.connect("Model",        "tvb_model",        "Simulator",  "tvb_model")
wf.connect("Coupling",     "tvb_coupling",     "Simulator",  "tvb_coupling")
wf.connect("Integrator",   "tvb_integrator",   "Simulator",  "tvb_integrator")
wf.connect("Monitor",      "tvb_monitor",      "Simulator",  "tvb_monitor")
wf.connect("Monitor2",     "tvb_monitor",      "Simulator",  "tvb_monitor_2")
wf.connect("Stimulus",     "tvb_stimulus",     "Simulator",  "tvb_stimulus")
wf.connect("Simulator",    "tvb_simdata",      "Plot",       "tvb_simdata")
wf.connect("Simulator",    "tvb_simtime",      "Plot",       "tvb_simtime")
wf.connect("Simulator",    "tvb_simdata_2",    "Plot2",      "tvb_simdata")
wf.connect("Simulator",    "tvb_simtime_2",    "Plot2",      "tvb_simtime")

workflow = wf.build()

# ── Execute ────────────────────────────────────────────────────────────────────

print(workflow)
print("\nExecuting...")
success = workflow.execute()
print("Done.\n" if success else "FAILED.\n")
