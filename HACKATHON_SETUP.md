# Hackathon Setup — PointNeuron Simulation Notebooks

The quickest path to running the BMTK/NEST point-neuron notebooks:

- `notebooks/NW_SingleCell_PointNeuron.ipynb`
- `notebooks/NW_Ring_PointNeuron.ipynb`
- `notebooks/NW_BalancedNetwork_PointNeuron.ipynb`

All three use BMTK PointNet with the builtin `nest:iaf_psc_alpha` model and
`compile_mechanisms=False`, so no custom NEST module compilation is needed.

## Choose a setup path

| | Path A — conda / mamba | Path B — venv + pip |
|---|---|---|
| Platforms | **All** (incl. older macOS, Linux aarch64, Windows/WSL) | macOS **15+** (arm64/x86_64) or Linux **x86_64** only |
| NEST source | conda-forge build | NEST PyPI wheel (CPython 3.9–3.13) |
| Best for | mixed laptops / "just works" | a single supported machine, lightweight |

If participants have mixed or older machines, prefer **Path A**. If you are on a
recent Mac (Apple Silicon / Intel, macOS 15+) or Linux x86_64 and want a plain
virtualenv, **Path B** works too.

## Get the code

The notebooks live in `notebooks/` and are **not** shipped by `pip install`, so
clone the repository:

```bash
git clone https://github.com/oist/neuro-workflow.git
cd neuro-workflow
```

(If you only want the notebook files without cloning, download them directly:)

```bash
for nb in NW_SingleCell_PointNeuron NW_Ring_PointNeuron NW_BalancedNetwork_PointNeuron; do
  curl -L -O "https://raw.githubusercontent.com/oist/neuro-workflow/main/notebooks/$nb.ipynb"
done
```

---

## Path A — conda / mamba (all platforms)

### 1. Get a conda / mamba launcher

If you already have `conda` or `mamba`, skip to step 2.

Otherwise install **Miniforge** — free, community-built, conda-forge default
channel, and it ships `mamba`:

| OS | Installer |
|----|-----------|
| macOS (Apple Silicon) | `Miniforge3-MacOSX-arm64.sh` |
| macOS (Intel)         | `Miniforge3-MacOSX-x86_64.sh` |
| Linux (x86_64)        | `Miniforge3-Linux-x86_64.sh` |
| Linux (aarch64)       | `Miniforge3-Linux-aarch64.sh` |

```bash
# pick the file for your OS from the table above:
URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"
curl -L -o Miniforge3.sh "$URL"
bash Miniforge3.sh -b
~/miniforge3/bin/conda init "$(basename "$SHELL")"
# restart your shell
```

> Miniforge uses the free conda-forge channel by default, so there are no
> Anaconda commercial-licensing concerns.

### 2. Create the environment

From the repository root:

```bash
bash setup_hackathon.sh
```

The script detects `mamba`/`conda` (or tells you to install Miniforge), creates
the `neuroworkflow-hackathon` environment from `environment.yml` (NEST + h5py +
JupyterLab from conda-forge), and installs `neuroworkflow[pointnet]` + `bmtk`
with pip. It is idempotent — re-running updates the environment.

Equivalent manual steps:

```bash
mamba env create -f environment.yml      # or: conda env create -f environment.yml
conda activate neuroworkflow-hackathon
pip install -e ".[pointnet]"
```

### 3. Launch JupyterLab

```bash
conda activate neuroworkflow-hackathon
cd notebooks
jupyter lab
```

---

## Path B — venv + pip (macOS 15+ / Linux x86_64)

Requires CPython **3.9–3.13** (NEST wheel range; 3.12 recommended) on macOS 15+
(arm64/x86_64) or Linux x86_64.

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-hackathon.txt   # neuroworkflow[pointnet,nest] + jupyterlab
cd notebooks
jupyter lab
```

`requirements-hackathon.txt` installs `-e .[pointnet,nest]` — i.e. neuroworkflow
plus `bmtk`/`h5py`/`matplotlib` (pointnet extra) plus `nest-simulator` from its
PyPI wheel (nest extra) — and `jupyterlab`.

Library-only install without cloning (then grab the notebooks as shown in
[Get the code](#get-the-code)):

```bash
pip install "neuroworkflow[pointnet,nest] @ git+https://github.com/oist/neuro-workflow.git"
pip install jupyterlab
```

> If `pip install nest-simulator` fails with a build/compile error, your
> platform has no NEST wheel (older macOS, Linux aarch64, Windows) — use
> **Path A** instead.

---

## Run the notebooks

Open any of the three notebooks and **Run All**. Outputs (SONATA network files,
spike/voltage reports, figures) are written under `notebooks/results/`.

> Run the notebooks with `notebooks/` as the working directory — they write to
> relative paths such as `./results/run1`.

## Smoke test (optional)

Verify the SingleCell notebook end-to-end without opening JupyterLab.

Path A (conda):

```bash
MPLBACKEND=Agg conda run -n neuroworkflow-hackathon \
  jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=600 \
  --output /tmp/NW_SingleCell_executed.ipynb \
  notebooks/NW_SingleCell_PointNeuron.ipynb
```

Path B (venv, with `.venv` activated):

```bash
MPLBACKEND=Agg jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=600 \
  --output /tmp/NW_SingleCell_executed.ipynb \
  notebooks/NW_SingleCell_PointNeuron.ipynb
```

## Notes

- **Apple Silicon (osx-arm64):** the NEST build (both conda-forge and the PyPI
  wheel) provides only the Mersenne-Twister RNGs (`mt19937`, `mt19937_64`).
  These notebooks use the default RNG and are unaffected — keep it in mind if
  you switch RNGs.
- **NEST version:** conda-forge resolves to 3.10; the PyPI wheel is also 3.10
  (aligned with the production `Dockerfile.nest`, NEST 3.9).
- **NEST PyPI wheel coverage:** macOS 15+ (arm64/x86_64) and Linux x86_64 only.
  Other platforms have no wheel — use Path A.
- **numpy:** both paths let the resolver pick a numpy 2.x that matches the
  NEST/h5py builds; do not pin `numpy<2`.
