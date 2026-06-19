"""
Leaky integrate-and-fire (LIF) recurrent network: quick simulation + analysis.

This is an intentionally UNSTRUCTURED example script — the kind of single-file,
top-to-bottom code a researcher might bring to the hackathon (parameters,
network construction, simulation, and analysis all mixed together). Use it as a
stand-in for "your own code":

    1. copy it into your working folder as  source_code/lif_network.py
    2. start your agent and run the create-node skill, pointing it at source_code/

A reasonable node breakdown the agent might propose:
    - a parameters / network-construction node  (stage: network)
    - a simulation node that runs the LIF dynamics and records spikes  (stage: simulation)
    - an analysis node that computes firing rate and a raster  (stage: analysis)

Runs with numpy alone (a core neuroworkflow dependency). The raster plot is saved
only if matplotlib is installed.
"""

import numpy as np

rng = np.random.default_rng(0)

# --- parameters -------------------------------------------------------------
N = 200            # number of neurons
p_conn = 0.1       # recurrent connection probability
w_exc = 0.5        # excitatory synaptic weight (mV per presynaptic spike)
tau_m = 20.0       # membrane time constant (ms)
v_rest = 0.0       # resting potential (mV)
v_thresh = 20.0    # spike threshold (mV)
v_reset = 0.0      # reset potential (mV)
t_ref = 2.0        # refractory period (ms)
i_ext = 22.0       # external drive (mV-equivalent; above threshold => regular firing)
dt = 0.1           # integration step (ms)
T = 1000.0         # total simulated time (ms)

# --- build a random recurrent connectivity matrix ---------------------------
W = (rng.random((N, N)) < p_conn).astype(float) * w_exc
np.fill_diagonal(W, 0.0)   # no self-connections

# --- simulate (forward Euler) -----------------------------------------------
n_steps = int(T / dt)
v = np.full(N, v_rest, dtype=float)
ref = np.zeros(N)          # remaining refractory time per neuron (ms)
spike_t = []               # spike times (ms)
spike_i = []               # spiking neuron indices

for step in range(n_steps):
    t = step * dt
    can_update = ref <= 0.0
    v[can_update] += (-(v[can_update] - v_rest) + i_ext) / tau_m * dt

    fired = np.where(can_update & (v >= v_thresh))[0]
    if fired.size:
        spike_t.extend([t] * fired.size)
        spike_i.extend(fired.tolist())
        v[fired] = v_reset
        ref[fired] = t_ref
        v += W[:, fired].sum(axis=1)   # deliver recurrent input

    ref -= dt

# --- analysis ---------------------------------------------------------------
n_spikes = len(spike_t)
mean_rate_hz = n_spikes / N / (T / 1000.0)
print(f"neurons={N}  total_spikes={n_spikes}  mean_firing_rate={mean_rate_hz:.2f} Hz")

# optional raster plot (saved to file if matplotlib is available)
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if spike_t:
        plt.figure(figsize=(8, 4))
        plt.scatter(spike_t, spike_i, s=2)
        plt.xlabel("time (ms)")
        plt.ylabel("neuron index")
        plt.title(f"LIF network raster (mean rate {mean_rate_hz:.1f} Hz)")
        plt.tight_layout()
        plt.savefig("lif_raster.png", dpi=100)
        print("saved lif_raster.png")
except ImportError:
    print("(matplotlib not installed — skipping raster plot)")
