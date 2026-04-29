"""
Workflow equivalent of:
    temp/models/TVB/TVB_1st_step_marmoset/1_TVB_First_steps.ipynb

One workflow is built and executed three times, reconfiguring nodes
between runs to match each simulation in the notebook:

  Sim 1 — Resting state (G2dOscillator a=1.74, HeunStochastic, Scaling)
  Sim 2 — Stimulus response (a=0.5, HeunDeterministic, Linear, Gaussian pulse)
  Sim 3 — BOLD signal (same as Sim 2, 60 s, Bold monitor, stimulus at 25 000 ms)
"""

import os

_HERE = os.path.dirname(os.path.abspath(__file__))
CONNECTIVITY_FILE = os.path.abspath(
    os.path.join(
        _HERE,
        "../../../../temp/models/TVB/TVB_1st_step_marmoset/dataset/connectivity_76.zip",
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

# ── Instantiate nodes (names are fixed; parameters change between runs) ────────

conn        = TVBConnectivitySetUpNode("Connectivity")
model       = TVBModelNode("Model")
coupling    = TVBCouplingNode("Coupling")
integrator  = TVBIntegratorNode("Integrator")
monitor     = TVBMonitorNode("Monitor")          # primary monitor
monitor2    = TVBMonitorNode("Monitor2")         # secondary monitor (Raw or Bold)
stimulus    = TVBStimuliRegionNode("Stimulus")   # present in all runs; zero weights = inactive
sim         = TVBSimulatorNode("Simulator")
plot        = TVBTimeSeriesPlotNode("Plot")

conn.configure(connectivity_file=CONNECTIVITY_FILE)

# ── Build topology once ────────────────────────────────────────────────────────

wf = WorkflowBuilder("TVB_FirstSteps")

wf.add_node(conn)
wf.add_node(model)
wf.add_node(coupling)
wf.add_node(integrator)
wf.add_node(monitor)
wf.add_node(monitor2)
wf.add_node(stimulus)
wf.add_node(sim)
wf.add_node(plot)

wf.connect("Connectivity", "tvb_connectivity", "Model",      "tvb_connectivity")
wf.connect("Connectivity", "tvb_connectivity", "Simulator",  "tvb_connectivity")
wf.connect("Connectivity", "tvb_connectivity", "Stimulus",   "tvb_connectivity")
wf.connect("Connectivity", "tvb_connectivity", "Plot",       "tvb_connectivity")
wf.connect("Model",        "tvb_model",        "Simulator",  "tvb_model")
wf.connect("Coupling",     "tvb_coupling",     "Simulator",  "tvb_coupling")
wf.connect("Integrator",   "tvb_integrator",   "Simulator",  "tvb_integrator")
wf.connect("Monitor",      "tvb_monitor",      "Simulator",  "tvb_monitor")
wf.connect("Monitor2",     "tvb_monitor",      "Simulator",  "tvb_monitor_2")
wf.connect("Stimulus",     "tvb_stimulus",     "Simulator",  "tvb_stimulus")
wf.connect("Simulator",    "tvb_simdata",      "Plot",       "tvb_simdata")
wf.connect("Simulator",    "tvb_simtime",      "Plot",       "tvb_simtime")

workflow = wf.build()

# ═══════════════════════════════════════════════════════════════════════════════
# SIM 1 — Resting state
# G2dOscillator a=1.74, HeunStochastic dt=0.1 ms, Scaling G=0.0075
# Monitors: TemporalAverage (100 Hz) + Raw
# No stimulus (zero weights)
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("SIM 1: Resting state")
print("=" * 60)

model.configure(model_type="Generic2dOscillator", model_params={"a": 1.74}, region_params={})
coupling.configure(coupling_type="Scaling", a=0.0075)
integrator.configure(integrator_type="HeunStochastic", dt=0.1, nsig=[0.001, 0.0])
monitor.configure(monitor_type="TemporalAverage", period=10.0)   # 100 Hz
monitor2.configure(monitor_type="Raw")
stimulus.configure(
    region_indices=[0, 7, 13, 33, 42],
    weights=[0.0, 0.0, 0.0, 0.0, 0.0],   # inactive — no stimulus in Sim 1
    temporal_equation="Gaussian",
    equation_params={"midpoint": 5000.0, "sigma": 1.0},
)
sim.configure(simulation_length=10000.0)
plot.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="Sim 1 — Resting State (TemporalAverage, 100 Hz)",
)

print(workflow)
print("\nExecuting...")
success = workflow.execute()
print("Sim 1 done.\n" if success else "Sim 1 FAILED.\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SIM 2 — Stimulus response
# G2dOscillator a=0.5, HeunDeterministic dt=0.5 ms, Linear a=0.0126
# Monitor: TemporalAverage (1 kHz)
# Gaussian stimulus: 5 regions, midpoint=4000 ms, sigma=200 ms
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("SIM 2: Stimulus response (Gaussian pulse at 4 000 ms)")
print("=" * 60)

model.configure(model_type="Generic2dOscillator", model_params={"a": 0.5}, region_params={})
coupling.configure(coupling_type="Linear", a=0.0126, b=0.0)
integrator.configure(integrator_type="HeunDeterministic", dt=0.5, nsig=[0.0, 0.0])
monitor.configure(monitor_type="TemporalAverage", period=1.0)
monitor2.configure(monitor_type="TemporalAverage", period=1.0)   # same as primary; unused output
stimulus.configure(
    region_indices=[0, 7, 13, 33, 42],
    weights=[2**-2, 2**-3, 2**-4, 2**-5, 2**-6],
    temporal_equation="Gaussian",
    equation_params={"midpoint": 4000.0, "sigma": 200.0},
)
sim.configure(simulation_length=10000.0)
plot.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="Sim 2 — Stimulus Response (Gaussian at 4 000 ms)",
)

print("\nExecuting...")
success = workflow.execute()
print("Sim 2 done.\n" if success else "Sim 2 FAILED.\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SIM 3 — BOLD signal
# Same model/coupling/integrator as Sim 2
# Monitors: TemporalAverage (1 kHz) + Bold (TR=500 ms)
# Stimulus midpoint shifted to 25 000 ms; simulation_length=60 000 ms
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("SIM 3: BOLD signal (60 s, stimulus at 25 000 ms)")
print("=" * 60)

# model, coupling, integrator same as Sim 2 — no reconfigure needed
monitor.configure(monitor_type="TemporalAverage", period=1.0)
monitor2.configure(monitor_type="Bold", period=500.0)
stimulus.configure(
    region_indices=[0, 7, 13, 33, 42],
    weights=[2**-2, 2**-3, 2**-4, 2**-5, 2**-6],
    temporal_equation="Gaussian",
    equation_params={"midpoint": 25000.0, "sigma": 200.0},
)
sim.configure(simulation_length=60000.0)
plot.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="Sim 3 — TemporalAverage (Bold simulation, stimulus at 25 000 ms)",
)

print("\nExecuting...")
success = workflow.execute()
print("Sim 3 done.\n" if success else "Sim 3 FAILED.\n")
