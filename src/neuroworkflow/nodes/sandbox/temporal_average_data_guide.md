# TVB Temporal Average Simulation Data Guide

## What is this data?

These files contain TemporalAverage neural activity simulations produced by The Virtual Brain (TVB) framework using a marmoset structural connectome (`connectivity_marmoset.zip`).

The TemporalAverage monitor records the mean neural state variable (V, the membrane potential) over a fixed time window — it is a direct, fast-timescale measure of neural dynamics, unlike BOLD which is a slow haemodynamic proxy.

Three simulation files are available:

| File | Duration | Sampling | Stimulus |
|---|---|---|---|
| `sim1_temporal_average.npz` | 30 s | 100 Hz (period=10 ms) | None (resting state) |
| `sim2_temporal_average.npz` | 60 s | 1 kHz (period=1 ms) | PulseTrain every 10 s (~5 pulses) |
| `sim3_temporal_average.npz` | 60 s | 1 kHz (period=1 ms) | PulseTrain, 2 pulses at 5 s and 35 s |

Stimulated regions: indices 0, 7, 13, 33, 42 — weights `[0.25, 0.125, 0.0625, 0.03125, 0.015625]`.

---

## File format

Each `.npz` file is a NumPy compressed archive. Load it with:

```python
import numpy as np

d = np.load("results/sim1_temporal_average.npz")
time = d["time"]   # shape: (n_timepoints,)           — time axis in milliseconds
data = d["data"]   # shape: (n_timepoints, n_regions) — neural activity, one column per region

n_timepoints, n_regions = data.shape
print(f"Time points: {n_timepoints}, Brain regions: {n_regions}")
```

- `time`: 1-D array of time points in **milliseconds**
- `data`: 2-D array, rows = time points, columns = brain regions
- Values represent the mean membrane potential V of the Generic2dOscillator model

---

## Region labels

```python
from tvb.simulator.lab import connectivity
conn = connectivity.Connectivity.from_file("connectivity_marmoset.zip")
region_labels = conn.region_labels   # shape: (n_regions,)
```

---

## Suggested visualizations

### 1. Time series for stimulated regions

```python
import matplotlib.pyplot as plt
import numpy as np

d = np.load("results/sim2_temporal_average.npz")
time = d["time"]
data = d["data"]

stimulated_regions = [0, 7, 13, 33, 42]
fig, ax = plt.subplots(figsize=(12, 6))
for i, r in enumerate(stimulated_regions):
    ax.plot(time / 1000, data[:, r] + i * 0.5, label=f"Region {r}")
ax.set_xlabel("Time [s]")
ax.set_ylabel("Neural activity (offset)")
ax.set_title("Sim 2 TemporalAverage — stimulated regions")
ax.legend()
plt.tight_layout()
plt.show()
```

### 2. Heatmap (all regions × time)

```python
n_timepoints, n_regions = data.shape

fig, ax = plt.subplots(figsize=(14, 8))
im = ax.imshow(data.T, aspect="auto", origin="lower",
               extent=[time[0] / 1000, time[-1] / 1000, 0, n_regions],
               cmap="RdBu_r")
ax.set_xlabel("Time [s]")
ax.set_ylabel("Region index")
ax.set_title(f"TemporalAverage — all {n_regions} regions")
plt.colorbar(im, ax=ax, label="V (membrane potential)")
plt.tight_layout()
plt.show()
```

### 3. Compare all 3 simulations for one region

```python
files = {
    "Sim 1 — Resting state": "results/sim1_temporal_average.npz",
    "Sim 2 — PulseTrain every 10 s": "results/sim2_temporal_average.npz",
    "Sim 3 — 2 pulses at 5 s and 35 s": "results/sim3_temporal_average.npz",
}

region = 0
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=False)
for ax, (title, path) in zip(axes, files.items()):
    d = np.load(path)
    ax.plot(d["time"] / 1000, d["data"][:, region])
    ax.set_title(f"{title} — Region {region}")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("V")
plt.tight_layout()
plt.show()
```

### 4. Compare TemporalAverage vs BOLD for same simulation

```python
ta = np.load("results/sim2_temporal_average.npz")
bold = np.load("results/sim2_bold.npz")

region = 0
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=False)
axes[0].plot(ta["time"] / 1000, ta["data"][:, region])
axes[0].set_title(f"Sim 2 — TemporalAverage, Region {region} (neural dynamics)")
axes[0].set_xlabel("Time [s]")
axes[0].set_ylabel("V")
axes[1].plot(bold["time"] / 1000, bold["data"][:, region])
axes[1].set_title(f"Sim 2 — BOLD, Region {region} (haemodynamic response)")
axes[1].set_xlabel("Time [s]")
axes[1].set_ylabel("BOLD")
plt.tight_layout()
plt.show()
```

This comparison clearly shows the difference in timescales: neural activity responds immediately to the stimulus, while the BOLD response is delayed by ~5 s and much slower to return to baseline.

---

## Quick start for Claude

Paste this file into your Claude conversation and say:

> "I have TVB TemporalAverage simulation data in `results/sim1_temporal_average.npz`, `results/sim2_temporal_average.npz`, and `results/sim3_temporal_average.npz`.
> Please load the data and create visualizations."
