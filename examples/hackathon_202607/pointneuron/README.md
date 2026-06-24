# Hackathon — PointNeuron Simulation Notebooks

Self-contained setup for running the BMTK/NEST point-neuron notebooks **without
cloning the repository**:

- `NW_SingleCell_PointNeuron.ipynb`
- `NW_Ring_PointNeuron.ipynb`
- `NW_BalancedNetwork_PointNeuron.ipynb`

All three use BMTK PointNet with the builtin `nest:iaf_psc_alpha` model and
`compile_mechanisms=False`, so no custom NEST module compilation is needed.

---

## Path A — venv + pip, no clone (recommended)

Works on **macOS 15+** (Apple Silicon / Intel) or **Linux x86_64** with
CPython **3.9–3.11** — the platforms NEST ships PyPI wheels for, within the
versions that still bundle the stdlib `distutils` that bmtk needs.

Download the one script and run it:

```bash
curl -fsSLO https://raw.githubusercontent.com/oist/neuro-workflow/main/examples/hackathon_202607/pointneuron/setup_pointneuron.sh
bash setup_pointneuron.sh
```

It creates a `.venv`, pip-installs `neuroworkflow[pointnet,nest]`
(neuroworkflow + `bmtk`/`h5py`/`matplotlib` + the NEST wheel) and `jupyterlab`
from a pinned ref, verifies the stack imports, and downloads the three
notebooks into `./notebooks`. It is idempotent — re-run any time.

> **Python version matters — use CPython 3.9–3.11.** bmtk imports the stdlib
> `distutils`, which was **removed in 3.12**, and NEST has no 3.14 wheel — so
> 3.12+ does not work for this stack. The script auto-selects a compatible
> interpreter from your `PATH`. If your only `python3` is 3.12+, install a
> supported one (`brew install python@3.11`) and re-run, pass
> `PYTHON=python3.11 bash setup_pointneuron.sh`, or use **Path B (conda)** below.

> **Before this PR is merged to `main`**, pin the branch:
> ```bash
> NW_REF=izumi/hackathon-pointneuron-setup bash setup_pointneuron.sh
> ```

Then:

```bash
source .venv/bin/activate          # bash/zsh  (fish: source .venv/bin/activate.fish)
jupyter lab
```

Open `notebooks/NW_SingleCell_PointNeuron.ipynb` (or Ring / BalancedNetwork) and
**Run All**. Outputs (SONATA network files, spike/voltage reports, figures) are
written under `notebooks/results/`.

---

## Path B — conda / mamba (all platforms)

Use this if `pip install nest-simulator` fails on your platform (older macOS,
Linux aarch64, Windows) — conda-forge has NEST builds for those too.

If you have neither `conda` nor `mamba`, install **Miniforge** (free,
conda-forge default channel, ships `mamba`):
<https://github.com/conda-forge/miniforge#install>. It avoids any Anaconda
commercial-licensing concern.

```bash
curl -fsSLO https://raw.githubusercontent.com/oist/neuro-workflow/main/examples/hackathon_202607/pointneuron/environment.yml
conda env create -f environment.yml          # or: mamba env create -f environment.yml
conda activate neuroworkflow-hackathon
pip install "neuroworkflow[pointnet] @ git+https://github.com/oist/neuro-workflow.git"

# download the three notebooks:
for nb in NW_SingleCell_PointNeuron NW_Ring_PointNeuron NW_BalancedNetwork_PointNeuron; do
  curl -fsSL -O "https://raw.githubusercontent.com/oist/neuro-workflow/main/notebooks/$nb.ipynb"
done

cd notebooks && jupyter lab    # or run jupyter lab and open the .ipynb files
```

---

## Developers (cloned checkout)

If you cloned the repo, install editable with both extras and run the notebooks
in place:

```bash
python3.11 -m venv .venv && source .venv/bin/activate   # use 3.9–3.11
pip install -e ".[pointnet,nest]"   # venv+pip;  or use Path B's environment.yml
cd notebooks && jupyter lab
```

## Smoke test (optional)

Verify the SingleCell notebook end-to-end without opening JupyterLab (venv
activated, or prefix with `conda run -n neuroworkflow-hackathon`):

```bash
MPLBACKEND=Agg jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=600 \
  --output /tmp/NW_SingleCell_executed.ipynb \
  notebooks/NW_SingleCell_PointNeuron.ipynb
```

## Notes

- **Apple Silicon (osx-arm64):** the NEST build (PyPI wheel and conda-forge)
  provides only the Mersenne-Twister RNGs (`mt19937`, `mt19937_64`). These
  notebooks use the default RNG and are unaffected — keep it in mind if you
  switch RNGs.
- **NEST version:** PyPI wheel and conda-forge both resolve to 3.10 (aligned
  with the production `Dockerfile.nest`, NEST 3.9).
- **NEST PyPI wheel coverage:** macOS 15+ (arm64/x86_64) and Linux x86_64 only;
  other platforms have no wheel — use Path B.
- **Python:** 3.9–3.11 only — bmtk imports the stdlib `distutils`, which was
  removed in 3.12.
- **numpy:** let the resolver pick a numpy 2.x matching the NEST/h5py builds;
  do not pin `numpy<2`.
- **pandas:** capped `<2.3` (via the `pointnet` extra). pandas 3.0 defaults
  string columns to `StringDtype`, which BMTK cannot hand to numpy
  ("Cannot interpret StringDtype as a data type").
- The `pointnet` (and `nest`) extras live in the repo-root `pyproject.toml`;
  `pip install "neuroworkflow[pointnet,nest]"` is what pulls the whole stack.
