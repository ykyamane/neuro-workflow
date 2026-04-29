# TVB BOLD Simulation Data Guide

## What is this data?

These files contain BOLD (Blood-Oxygen-Level-Dependent) fMRI signal simulations produced by The Virtual Brain (TVB) framework using a marmoset structural connectome (`connectivity_marmoset.zip`).

The BOLD signal is computed from neural activity via a haemodynamic response model (TVB Bold monitor, TR = 500 ms). It represents what a real fMRI scanner would measure — a slow, delayed signal reflecting underlying neural activity.

Three simulation files are available:

| File | Duration | Stimulus |
|---|---|---|
| `sim1_bold.npz` | 30 s | None (resting state) |
| `sim2_bold.npz` | 60 s | PulseTrain every 10 s (~5 pulses) |
| `sim3_bold.npz` | 60 s | PulseTrain, 2 pulses at 5 s and 35 s |

Stimulated regions: indices 0, 7, 13, 33, 42 — weights `[0.25, 0.125, 0.0625, 0.03125, 0.015625]`.

---

## File format

Each `.npz` file is a NumPy compressed archive. Load it with:

```python
import numpy as np

d = np.load("results/sim1_bold.npz")
time = d["time"]   # shape: (n_timepoints,)           — time axis in milliseconds
bold = d["data"]   # shape: (n_timepoints, n_regions) — BOLD signal, one column per region

n_timepoints, n_regions = bold.shape
print(f"Time points: {n_timepoints}, Brain regions: {n_regions}")
```

- `time`: 1-D array of time points in **milliseconds**
- `data`: 2-D array, rows = time points, columns = brain regions
- BOLD signal is dimensionless (relative signal change)

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

d = np.load("results/sim2_bold.npz")
time = d["time"]
bold = d["data"]

stimulated_regions = [0, 7, 13, 33, 42]
fig, ax = plt.subplots(figsize=(12, 6))
for i, r in enumerate(stimulated_regions):
    ax.plot(time / 1000, bold[:, r] + i * 0.01, label=f"Region {r}")
ax.set_xlabel("Time [s]")
ax.set_ylabel("BOLD signal (offset)")
ax.set_title("Sim 2 BOLD — stimulated regions")
ax.legend()
plt.tight_layout()
plt.show()
```

### 2. Heatmap (all regions × time)

```python
n_timepoints, n_regions = bold.shape

fig, ax = plt.subplots(figsize=(14, 8))
im = ax.imshow(bold.T, aspect="auto", origin="lower",
               extent=[time[0] / 1000, time[-1] / 1000, 0, n_regions])
ax.set_xlabel("Time [s]")
ax.set_ylabel("Region index")
ax.set_title(f"BOLD signal — all {n_regions} regions")
plt.colorbar(im, ax=ax, label="BOLD")
plt.tight_layout()
plt.show()
```

### 3. Compare all 3 simulations for one region

```python
files = {
    "Sim 1 — Resting state": "results/sim1_bold.npz",
    "Sim 2 — PulseTrain every 10 s": "results/sim2_bold.npz",
    "Sim 3 — 2 pulses at 5 s and 35 s": "results/sim3_bold.npz",
}

region = 0
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=False)
for ax, (title, path) in zip(axes, files.items()):
    d = np.load(path)
    ax.plot(d["time"] / 1000, d["data"][:, region])
    ax.set_title(f"{title} — Region {region}")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("BOLD")
plt.tight_layout()
plt.show()
```

### 4. Functional connectivity matrix (BOLD correlations)

```python
fc = np.corrcoef(bold.T)   # shape: (n_regions, n_regions)

fig, ax = plt.subplots(figsize=(8, 7))
im = ax.imshow(fc, vmin=-1, vmax=1, cmap="RdBu_r")
ax.set_title("Functional Connectivity (BOLD correlations)")
ax.set_xlabel("Region index")
ax.set_ylabel("Region index")
plt.colorbar(im, ax=ax, label="Pearson r")
plt.tight_layout()
plt.show()
```

---

## Quick start for Claude

Paste this file into your Claude conversation and say:

> "I have TVB BOLD simulation data in `results/sim1_bold.npz`, `results/sim2_bold.npz`, and `results/sim3_bold.npz`.
> Please load the data and create visualizations."
