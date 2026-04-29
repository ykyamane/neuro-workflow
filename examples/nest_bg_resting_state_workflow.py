"""
NEST 3 Basal Ganglia — Resting State Workflow
==============================================
Runs the 4 BG nodes end-to-end:

  NESTBGParametersNode  →  NESTBGNetworkNode
                        →  NESTBGSimulationNode
                        →  NESTBGWriterNode

Outputs are written to ./results/ (relative to where this script runs).

QUICK TEST   (~2 min):  scale_factor=0.3, sim_duration_ms=1500
FULL RUN     (~5 min):  sim_duration_ms=3000  (matches Girard et al.)

Usage
-----
  # From repo root, with NEST installed in the active environment:
  python examples/nest_bg_resting_state_workflow.py

  # Or inside a Jupyter notebook/JupyterHub kernel:
  %run examples/nest_bg_resting_state_workflow.py

Expected resting-state firing rates (validation targets from Girard et al.):
  MSN    0.05–1.0  Hz   GPe   55.7–74.5 Hz
  FSI    7.8–14.0  Hz   GPi   59.1–79.5 Hz
  STN   15.2–22.8  Hz
"""

from neuroworkflow import WorkflowBuilder

from neuroworkflow.nodes.simulation.NESTBGParametersNode import NESTBGParametersNode
from neuroworkflow.nodes.network.NESTBGNetworkNode      import NESTBGNetworkNode
from neuroworkflow.nodes.simulation.NESTBGSimulationNode import NESTBGSimulationNode
from neuroworkflow.nodes.io.NESTBGWriterNode            import NESTBGWriterNode

# ── Instantiate nodes ──────────────────────────────────────────────────────────

params = NESTBGParametersNode("Parameters")
network = NESTBGNetworkNode("Network")
sim     = NESTBGSimulationNode("Simulation")
writer  = NESTBGWriterNode("Writer")

# ── Configure parameters ───────────────────────────────────────────────────────
# Change these to explore the parameter space.

params.configure(
    # ── Simulation timing ──────────────────────────────────────────────────
    # Fast test: sim_duration_ms=1500, warmup_ms=300
    # Full run:  sim_duration_ms=3000, warmup_ms=1000
    sim_duration_ms = 1500.0,
    warmup_ms       = 300.0,
    dt_ms           = 0.1,

    # ── NEST kernel ────────────────────────────────────────────────────────
    n_threads  = 10,
    rng_seed   = 42,

    # ── Population size ────────────────────────────────────────────────────
    # 0.3 → 30 % of neurons per nucleus (scalefactor = [0.3, 1.0] internally).
    # MSN ~9 500, FSI ~190, STN ~28, GPe ~90, GPi ~50.
    # FSI→MSN drops from ~138 M to ~41 M synapses — ~3× faster to build.
    # Full scale: scale_factor=1.0
    scale_factor = 0.3,

    # DC drive currents [pA] — tune to hit target firing rates
    ie_msn_pa = 26.0,
    ie_fsi_pa = 8.0,
    ie_gpe_pa = 11.0,
    ie_gpi_pa = 8.5,
    ie_stn_pa = 9.0,

    # Striatal pathway balance
    overlap_d1d2 = 0.1,   # λ: D1/D2 overlap (0=segregated, 0.5=50% overlap)
    syn_asymm    = 2.0,   # κ: D2→MSN weight multiplier

    # Output location
    output_dir = "./results",
)

writer.configure(output_dir="./results")

# ── Build workflow topology ────────────────────────────────────────────────────

wf = WorkflowBuilder("NEST_BG_RestingState")

wf.add_node(params)
wf.add_node(network)
wf.add_node(sim)
wf.add_node(writer)

# Parameters → Network
wf.connect("Parameters", "bg_params",  "Network", "bg_params")
wf.connect("Parameters", "sim_params", "Network", "sim_params")

# Network → Simulation
wf.connect("Network", "bg_layers",       "Simulation", "bg_layers")
wf.connect("Network", "spike_detectors", "Simulation", "spike_detectors")
wf.connect("Network", "sim_params",      "Simulation", "sim_params")

# Simulation → Writer
wf.connect("Simulation", "mean_fr",    "Writer", "mean_fr")
wf.connect("Simulation", "at_fr",      "Writer", "at_fr")
wf.connect("Simulation", "sim_params", "Writer", "sim_params")

# Network → Writer (positions + GIDs come from live bg_layers)
wf.connect("Network", "bg_layers", "Writer", "bg_layers")

workflow = wf.build()

# ── Run ────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("NEST BG Resting State — workflow topology")
print("=" * 60)
print(workflow)
print("\nStarting execution...\n")

success = workflow.execute()

if success:
    print("\n✓  Workflow completed successfully.")
    print("   Results in: ./results/")
    print("     mean_fr.json           — mean firing rates per nucleus")
    print("     At.json                — 1-ms-binned instantaneous rates")
    print("     populations/<nucleus>/ — gids.npy, positions.npy, spikes.npz")
else:
    print("\n✗  Workflow FAILED — check output above for errors.")
