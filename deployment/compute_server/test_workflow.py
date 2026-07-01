"""Lightweight, self-contained workflow for validating the remote Slurm pipe.

No simulator and no network access - just numpy. It proves the full loop
(stage -> rsync -> sbatch -> sacct -> result retrieval) end to end. Outputs are
written into the per-run directory (the job runs with --chdir into it), which
lives on /data/neuro-workflow, so nothing touches the OS /tmp.
"""

import json
import platform

import numpy as np

rng = np.random.default_rng(42)
x = rng.normal(size=10_000)

summary = {
    "node": platform.node(),
    "python": platform.python_version(),
    "numpy": np.__version__,
    "n": int(x.size),
    "mean": float(x.mean()),
    "std": float(x.std()),
}

print("NeuroWorkflow remote-pipe test")
for key, value in summary.items():
    print(f"  {key}: {value}")

with open("result.json", "w") as fh:
    json.dump(summary, fh, indent=2)

print("wrote result.json")
