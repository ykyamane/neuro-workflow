"""
Workflow equivalent of:
    temp/models/TVB/TVB_1st_step_marmoset/1_TVB_First_steps.ipynb

One workflow is built and executed three times, reconfiguring nodes between runs.
All simulations record TemporalAverage + BOLD and save both to file.

  Sim 1 — Resting state, 30 s (G2dOscillator a=1.74, HeunStochastic, Scaling, no stimulus)
  Sim 2 — Stimulus response, 60 s (a=0.5, HeunDeterministic, Linear, PulseTrain every 10 s)
  Sim 3 — BOLD demonstration, 60 s (same as Sim 2, 2 pulses at 5 s and 35 s)

Output files (./results/):
  sim1_temporal_average.npz, sim1_bold.npz
  sim2_temporal_average.npz, sim2_bold.npz
  sim3_temporal_average.npz, sim3_bold.npz
"""

import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()  # Jupyter: CWD is the sandbox directory

CONNECTIVITY_FILE = os.path.abspath(
    os.path.join(
        _HERE,
        "../data/tvb_data/connectivity_marmoset.zip",
    )
)

from neuroworkflow import WorkflowBuilder
from neuroworkflow.nodes.network.TVBConnectivitySetUpNode import TVBConnectivitySetUpNode
from neuroworkflow.nodes.network.TVBModelNodeV2 import TVBModelNodeV2
from neuroworkflow.nodes.network.TVBCouplingNodeV2 import TVBCouplingNodeV2
from neuroworkflow.nodes.simulation.TVBIntegratorNodeV2 import TVBIntegratorNodeV2
from neuroworkflow.nodes.simulation.TVBMonitorNodeV2 import TVBMonitorNodeV2
from neuroworkflow.nodes.simulation.TVBSimulatorNodeV2 import TVBSimulatorNodeV2
from neuroworkflow.nodes.stimulus.TVBStimuliRegionNodeV2 import TVBStimuliRegionNodeV2
from neuroworkflow.nodes.analysis.TVBTimeSeriesPlotNodeV2 import TVBTimeSeriesPlotNodeV2

# ── Instantiate nodes (names are fixed; parameters change between runs) ────────

conn        = TVBConnectivitySetUpNode("Connectivity")
model       = TVBModelNodeV2("Model")
coupling    = TVBCouplingNodeV2("Coupling")
integrator  = TVBIntegratorNodeV2("Integrator")
monitor     = TVBMonitorNodeV2("Monitor")          # primary monitor
monitor2    = TVBMonitorNodeV2("Monitor2")         # secondary monitor (Bold)
stimulus    = TVBStimuliRegionNodeV2("Stimulus")   # present in all runs; zero weights = inactive
sim         = TVBSimulatorNodeV2("Simulator")
plot        = TVBTimeSeriesPlotNodeV2("Plot")    # primary monitor output
plot2       = TVBTimeSeriesPlotNodeV2("Plot2")   # secondary monitor output (Bold)

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
wf.add_node(plot2)

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
wf.connect("Simulator",    "tvb_simdata_2",    "Plot2",      "tvb_simdata")
wf.connect("Simulator",    "tvb_simtime_2",    "Plot2",      "tvb_simtime")
wf.connect("Connectivity", "tvb_connectivity", "Plot2",      "tvb_connectivity")

workflow = wf.build()

# ═══════════════════════════════════════════════════════════════════════════════
# SIM 1 — Resting state
# G2dOscillator a=1.74, HeunStochastic dt=0.5 ms, Scaling G=0.0075
# Monitors: TemporalAverage (100 Hz) + Bold (TR=500 ms)
# No stimulus (zero weights)
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("SIM 1: Resting state")
print("=" * 60)

model.configure(model_type="Generic2dOscillator", model_params={"a": 1.74}, region_params={})
coupling.configure(coupling_type="Scaling", a=0.0075)
integrator.configure(integrator_type="HeunStochastic", dt=0.5, nsig=[0.001, 0.0])
monitor.configure(monitor_type="TemporalAverage", period=10.0)   # 100 Hz
monitor2.configure(monitor_type="Bold", period=500.0)
stimulus.configure(
    region_indices=[0, 7, 13, 33, 42],
    weights=[0.0, 0.0, 0.0, 0.0, 0.0],   # zero weights — change to [0.25, 0.125, 0.0625, 0.03125, 0.015625] to activate
    temporal_equation="PulseTrain",
    equation_params={"T": 10000.0, "tau": 1000.0, "amp": 1.0, "onset": 5000.0},
    simulation_length=30000.0,
)
sim.configure(simulation_length=30000.0)
plot.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="Sim 1 — Resting State (TemporalAverage, 100 Hz)",
    save_to_file=True, output_path="./results/sim1_temporal_average.npz",
)
plot2.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="Sim 1 — Resting State BOLD (TR=500 ms)",
    save_to_file=True, output_path="./results/sim1_bold.npz",
)

print(workflow)
print("\nExecuting...")
success = workflow.execute()
print("Sim 1 done.\n" if success else "Sim 1 FAILED.\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SIM 2 — Stimulus response
# G2dOscillator a=0.5, HeunDeterministic dt=0.5 ms, Linear a=0.0126
# Monitor: TemporalAverage (1 kHz) + Bold (TR=500 ms)
# PulseTrain stimulus: 5 regions, pulse every 10 s, width=1 s, onset=5 000 ms
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("SIM 2: Stimulus response (PulseTrain, pulse every 10 s)")
print("=" * 60)

model.configure(model_type="Generic2dOscillator", model_params={"a": 0.5}, region_params={})
coupling.configure(coupling_type="Linear", a=0.0126, b=0.0)
integrator.configure(integrator_type="HeunDeterministic", dt=0.5, nsig=[0.0, 0.0])
monitor.configure(monitor_type="TemporalAverage", period=1.0)
monitor2.configure(monitor_type="Bold", period=500.0)
stimulus.configure(
    region_indices=[0, 7, 13, 33, 42],
    weights=[2**-2, 2**-3, 2**-4, 2**-5, 2**-6],
    temporal_equation="PulseTrain",
    equation_params={"T": 10000.0, "tau": 1000.0, "amp": 1.0, "onset": 5000.0},
    simulation_length=60000.0,
)
sim.configure(simulation_length=60000.0)
plot.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="Sim 2 — Stimulus Response (TemporalAverage, PulseTrain every 10 s)",
    save_to_file=True, output_path="./results/sim2_temporal_average.npz",
)
plot2.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="Sim 2 — BOLD Signal (PulseTrain every 10 s)",
    save_to_file=True, output_path="./results/sim2_bold.npz",
)

print("\nExecuting...")
success = workflow.execute()
print("Sim 2 done.\n" if success else "Sim 2 FAILED.\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SIM 3 — BOLD signal
# Same model/coupling/integrator as Sim 2
# Monitors: TemporalAverage (1 kHz) + Bold (TR=500 ms)
# PulseTrain stimulus: 2 pulses only (T=30 s, onset=5 s, pulses at 5 s and 35 s)
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("SIM 3: BOLD signal (60 s, 2 pulses at 5 s and 35 s)")
print("=" * 60)

# model, coupling, integrator same as Sim 2 — no reconfigure needed
monitor.configure(monitor_type="TemporalAverage", period=1.0)
monitor2.configure(monitor_type="Bold", period=500.0)
stimulus.configure(
    region_indices=[0, 7, 13, 33, 42],
    weights=[2**-2, 2**-3, 2**-4, 2**-5, 2**-6],
    temporal_equation="PulseTrain",
    equation_params={"T": 30000.0, "tau": 1000.0, "amp": 1.0, "onset": 5000.0},
    simulation_length=60000.0,
)
sim.configure(simulation_length=60000.0)
plot.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="Sim 3 — TemporalAverage (2 pulses at 5 s and 35 s)",
    save_to_file=True, output_path="./results/sim3_temporal_average.npz",
)
plot2.configure(
    n_regions=10, state_variable_index=0, normalize=True,
    title="Sim 3 — BOLD Signal (TR=500 ms, 2 pulses at 5 s and 35 s)",
    save_to_file=True, output_path="./results/sim3_bold.npz",
)

print("\nExecuting...")
success = workflow.execute()
print("Sim 3 done.\n" if success else "Sim 3 FAILED.\n")
