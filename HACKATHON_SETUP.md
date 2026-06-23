# Hackathon Setup — PointNeuron Simulation Notebooks

The quickest path to running the BMTK/NEST point-neuron notebooks:

- `notebooks/NW_SingleCell_PointNeuron.ipynb`
- `notebooks/NW_Ring_PointNeuron.ipynb`
- `notebooks/NW_BalancedNetwork_PointNeuron.ipynb`

NEST cannot be installed reliably with `pip`, so we install it (and the
ABI-linked `h5py`/`numpy`) from **conda-forge**, and install NeuroWorkflow +
BMTK with `pip` inside that environment.

## 1. Get a conda / mamba launcher

If you already have `conda` or `mamba`, skip to step 2.

Otherwise install **Miniforge** — free, community-built, conda-forge default
channel, and it ships `mamba`:

| OS | Installer |
|----|-----------|
| macOS (Apple Silicon) | `Miniforge3-MacOSX-arm64.sh` |
| macOS (Intel)         | `Miniforge3-MacOSX-x86_64.sh` |
| Linux (x86_64)        | `Miniforge3-Linux-x86_64.sh` |

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

## 2. Create the environment

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

## 3. Run the notebooks

```bash
conda activate neuroworkflow-hackathon
cd notebooks
jupyter lab
```

Open any of the three notebooks and **Run All**. Outputs (SONATA network files,
spike/voltage reports, figures) are written under `notebooks/results/`.

> Run the notebooks with `notebooks/` as the working directory — they write to
> relative paths such as `./results/run1`.

## Smoke test (optional)

Verify the SingleCell notebook end-to-end without opening JupyterLab:

```bash
MPLBACKEND=Agg conda run -n neuroworkflow-hackathon \
  jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=600 \
  --output /tmp/NW_SingleCell_executed.ipynb \
  notebooks/NW_SingleCell_PointNeuron.ipynb
```

## Notes

- **Apple Silicon (osx-arm64):** the conda-forge NEST build provides only the
  Mersenne-Twister RNGs (`mt19937`, `mt19937_64`). These notebooks use the
  default RNG and are unaffected — keep it in mind if you switch RNGs.
- **NEST version:** `environment.yml` pins `nest-simulator>=3.8,<3.11` (resolves
  to 3.10 on conda-forge), aligned with the production `Dockerfile.nest`
  (NEST 3.9).
- **numpy:** let conda resolve numpy (2.x) to match the NEST/h5py builds; do not
  pin `numpy<2`.
- These notebooks use BMTK PointNet with the builtin `nest:iaf_psc_alpha` model
  and `compile_mechanisms=False`, so no custom NEST module compilation is
  needed.
