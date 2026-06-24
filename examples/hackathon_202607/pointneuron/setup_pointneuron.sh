#!/usr/bin/env bash
#
# Hackathon one-command setup for the NeuroWorkflow PointNeuron simulation
# notebooks — WITHOUT cloning the repository.
#
#   Usage:   bash setup_pointneuron.sh
#
# Re-runnable (idempotent). Creates a Python venv, pip-installs
# neuroworkflow[pointnet,nest] (neuroworkflow + bmtk/h5py/matplotlib + NEST's
# PyPI wheel) and jupyterlab from a pinned ref, then downloads the three
# PointNeuron notebooks into ./notebooks.
#
# NEST publishes PyPI wheels only for macOS 15+ (arm64/x86_64) and Linux x86_64
# (CPython 3.9-3.13). On other platforms (older macOS, Linux aarch64, Windows)
# use the conda path in README.md instead.
set -euo pipefail

# ---- Configuration ----------------------------------------------------------
VENV_DIR="${VENV_DIR:-.venv}"                                 # python venv folder
PYTHON="${PYTHON:-python3}"                                   # base interpreter
# Pin neuro-workflow to a ref so every participant gets the SAME package AND the
# same notebooks. Bump this to upgrade everyone at once. Until the hackathon
# branch is merged, run with:  NW_REF=izumi/hackathon-pointneuron-setup bash ...
NW_REF="${NW_REF:-main}"
RAW="https://raw.githubusercontent.com/oist/neuro-workflow/${NW_REF}"
NOTEBOOKS=(NW_SingleCell_PointNeuron NW_Ring_PointNeuron NW_BalancedNetwork_PointNeuron)

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[0;32m✓ %s\033[0m\n' "$*"; }
trap 'printf "\n\033[1;31m✗ setup_pointneuron.sh failed (line %s). Re-run after fixing the error above.\033[0m\n" "$LINENO"' ERR

# ---- 1. Python virtual environment -----------------------------------------
step "[1/4] Python virtual environment (./${VENV_DIR})"
if [ ! -x "${VENV_DIR}/bin/python" ]; then
  "$PYTHON" -m venv "$VENV_DIR"
  ok "created venv with $("$PYTHON" --version 2>&1)"
else
  ok "reusing existing venv ($("${VENV_DIR}/bin/python" --version 2>&1))"
fi
PYBIN="${VENV_DIR}/bin/python"        # call these directly — no activate needed,
PIPBIN="${VENV_DIR}/bin/pip"          # so this works regardless of fish/bash/zsh.

# ---- 2. Dependencies (pinned, no clone) ------------------------------------
step "[2/4] Installing neuroworkflow[pointnet,nest] + jupyterlab (pinned to ${NW_REF})"
"$PYBIN" -m pip install --upgrade pip >/dev/null
"$PIPBIN" install \
  "neuroworkflow[pointnet,nest] @ git+https://github.com/oist/neuro-workflow.git@${NW_REF}" \
  jupyterlab
ok "neuroworkflow + bmtk + NEST wheel + jupyterlab installed"

# ---- 3. Verify the simulation stack imports --------------------------------
step "[3/4] Verifying the simulation stack"
"$PYBIN" - <<'PY'
from neuroworkflow import WorkflowBuilder
from neuroworkflow.nodes.network.NW_Population import NW_Population
import bmtk, nest, h5py, matplotlib  # noqa: F401
print("    neuroworkflow / bmtk / nest / h5py / matplotlib OK")
PY

# ---- 4. Download the PointNeuron notebooks (no clone) ----------------------
step "[4/4] Downloading PointNeuron notebooks into ./notebooks"
mkdir -p notebooks
for nb in "${NOTEBOOKS[@]}"; do
  curl -fsSL -o "notebooks/${nb}.ipynb" "${RAW}/notebooks/${nb}.ipynb"
  ok "notebooks/${nb}.ipynb"
done

# ---- Done -------------------------------------------------------------------
step "Setup complete ✅"
cat <<EOF

Next steps:
  1. Activate the venv:
       source ${VENV_DIR}/bin/activate           # bash / zsh
       source ${VENV_DIR}/bin/activate.fish       # fish
  2. Launch JupyterLab:
       jupyter lab
  3. Open notebooks/${NOTEBOOKS[0]}.ipynb (or Ring / BalancedNetwork) and
     Run All. Outputs are written under notebooks/results/.
EOF
