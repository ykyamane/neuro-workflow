# Understand the Brain Connectivity Viewer

Help the user reason about the interactive 3D marmoset brain connectivity viewer produced by `TVBMarmosetBrainViewerNode`. Apply this skill when the user asks about "the viewer", "the brain", a selected region, connections/weights, BOLD activity, stimulated regions, or pastes a **viewer state snapshot** (a Markdown block titled `# Brain Connectivity Viewer — current state`).

There are two distinct things the user may mean by "the brain state":

1. **Live view state** — what is on screen right now (selected region, threshold, BOLD frame, toggles). The user delivers this by clicking **"📋 Copy state for Chat"** in the viewer and pasting the snapshot. Trust the pasted Markdown and its embedded ` ```json ``` ` block directly — no file read needed. Summarise or answer from it.

2. **Underlying data** — the full connectome the viewer draws. This lives on disk and you read it with `run_code` / `read_file`. Use it for questions the snapshot can't answer (e.g. "which regions does X connect to most strongly?", "top BOLD regions at t=…").

## Where the data lives

The viewer writes three files into the node's `output_dir`, inside the project folder:

```
/home/jovyan/codes/projects/<project_id>/<output_dir>/connectivity_data.json
```

`output_dir` defaults to `results/viewer` but is a node parameter, so it can differ. If unsure, search: `run_code("import glob; print(glob.glob('/home/jovyan/codes/projects/**/connectivity_data.json', recursive=True))")`.

## connectivity_data.json schema

Top-level keys: `meta`, `regions`, `connections`, `bold`, `mesh`, `tracts`.

- `meta`: `n_regions`, `n_connections`, `weight_min_nz`, `weight_max`, `area_min`, `area_max`, `area_spheres` (bool), `hemi_colors` (bool), `stimulated_regions` (list of region **indices**), `stimulated_region_weights`.
- `regions`: list of `{name, x, y, z, hemi, area}`. `hemi` is `"L"` or `"R"` (names also start with `L_`/`R_`). `area` is surface area in mm². Index into this list is the region id used everywhere else.
- `connections`: list of `[i, j, weight, tract_length]`, where `i`/`j` are region indices, `weight` is structural connection strength, `tract_length` is in mm. **Sorted by weight descending** — the strongest edges come first.
- `bold` (or `null`): `{time: [ms,...], data: [[value per region], ...]}` indexed `data[timepoint][region]`. Present only when the node ran with BOLD/TemporalAverage timeseries.
- `mesh`: brain surface geometry (`v` vertices, `f` faces) — for rendering, rarely needed for analysis.
- `tracts` (or `null`): anatomical fiber paths keyed `"min(i,j),max(i,j)"`.

(Source of truth: `src/neuroworkflow/nodes/io/TVBMarmosetBrainViewerNode.py`.)

## Common run_code recipes

Load once:

```python
import json, glob
path = glob.glob('/home/jovyan/codes/projects/**/connectivity_data.json', recursive=True)[0]
D = json.load(open(path))
names = [r['name'] for r in D['regions']]
```

Strongest connections of a named region (connections are pre-sorted by weight):

```python
idx = names.index('L_A10')
hits = [c for c in D['connections'] if idx in (c[0], c[1])][:5]
for i, j, w, length in hits:
    other = j if i == idx else i
    print(names[other], w)
```

Most active regions at a BOLD timepoint:

```python
import numpy as np
t = 10  # frame index; D['bold']['time'][t] gives the time in ms
row = D['bold']['data'][t]
for k in np.argsort(row)[::-1][:5]:
    print(names[k], row[k])
```

Resolve stimulated region names:

```python
print([names[i] for i in D['meta']['stimulated_regions']])
```

## Guidance

- A pasted snapshot reflects a *moment* in the user's session; the on-disk JSON is the *whole* dataset. If the user asks "what am I looking at", prefer the snapshot; if they ask for analysis beyond it, read the JSON.
- Always verify a region name exists in `names` before indexing; report clearly if it doesn't.
- Weights are unitless structural strengths — describe them relatively ("strongest", "top 5"), not as physical quantities.
