#!/usr/bin/env bash
#
# Hackathon one-command setup for the NeuroWorkflow PointNeuron simulation
# notebooks — WITHOUT cloning the repository.
#
#   Usage:   bash setup_pointneuron.sh
#            PYTHON=python3.12 bash setup_pointneuron.sh   # force an interpreter
#
# Re-runnable (idempotent). Selects a NEST-compatible Python, creates a venv,
# pip-installs neuroworkflow[pointnet,nest] (neuroworkflow + bmtk/h5py/matplotlib
# + NEST's PyPI wheel) and jupyterlab from a pinned ref, then downloads the three
# PointNeuron notebooks into ./notebooks.
#
# NEST publishes PyPI wheels only for macOS 15+ (arm64/x86_64) and Linux x86_64,
# and only for CPython 3.9-3.13 (no 3.14 wheel yet). On unsupported platforms or
# Python versions, use the conda path in README.md instead.
set -euo pipefail

# ---- Configuration ----------------------------------------------------------
VENV_DIR="${VENV_DIR:-.venv}"                                 # python venv folder
# Pin neuro-workflow to a ref so every participant gets the SAME package AND the
# same notebooks. Bump this to upgrade everyone at once. Until the hackathon
# branch is merged, run with:  NW_REF=izumi/hackathon-pointneuron-setup bash ...
NW_REF="${NW_REF:-main}"
RAW="https://raw.githubusercontent.com/oist/neuro-workflow/${NW_REF}"
NOTEBOOKS=(NW_SingleCell_PointNeuron NW_Ring_PointNeuron NW_BalancedNetwork_PointNeuron)

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[0;32m✓ %s\033[0m\n' "$*"; }
trap 'printf "\n\033[1;31m✗ setup_pointneuron.sh failed (line %s). Re-run after fixing the error above.\033[0m\n" "$LINENO"' ERR

# True if the given interpreter is CPython 3.9-3.13 (the NEST wheel range).
py_compatible() {
  "$1" -c 'import sys; raise SystemExit(0 if (3,9) <= sys.version_info[:2] <= (3,13) else 1)' >/dev/null 2>&1
}

# ---- 1. Select a NEST-compatible Python (3.9-3.13) -------------------------
step "[1/5] Selecting a NEST-compatible Python (3.9-3.13)"
PYBASE=""
for cand in "${PYTHON:-}" python3.12 python3.11 python3.13 python3.10 python3.9 python3; do
  [ -n "$cand" ] || continue
  command -v "$cand" >/dev/null 2>&1 || continue
  if py_compatible "$cand"; then PYBASE="$cand"; break; fi
done
if [ -z "$PYBASE" ]; then
  printf '\033[1;31m'
  cat >&2 <<'MSG'
    No CPython 3.9-3.13 found. NEST's PyPI wheels do not cover 3.14+, so pip
    would try to build NEST from source and fail (needs GSL/OpenMP/ninja/...).
    Fix one of:
      • Install a supported Python and re-run, e.g.:
          brew install python@3.12
          PYTHON=python3.12 bash setup_pointneuron.sh
      • Or use the conda path (all platforms) — see README.md (Path B).
MSG
  printf '\033[0m'
  exit 1
fi
ok "using $("$PYBASE" --version 2>&1) ($PYBASE)"

# ---- 2. Python virtual environment -----------------------------------------
step "[2/5] Python virtual environment (./${VENV_DIR})"
if [ -x "${VENV_DIR}/bin/python" ] && py_compatible "${VENV_DIR}/bin/python"; then
  ok "reusing existing venv ($("${VENV_DIR}/bin/python" --version 2>&1))"
else
  if [ -e "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"                       # remove a stale/incompatible venv
    ok "removed incompatible existing venv"
  fi
  "$PYBASE" -m venv "$VENV_DIR"
  ok "created venv with $("$PYBASE" --version 2>&1)"
fi
PYBIN="${VENV_DIR}/bin/python"        # call these directly — no activate needed,
PIPBIN="${VENV_DIR}/bin/pip"          # so this works regardless of fish/bash/zsh.

# ---- 3. Dependencies (pinned, no clone) ------------------------------------
step "[3/5] Installing neuroworkflow[pointnet,nest] + jupyterlab (pinned to ${NW_REF})"
"$PYBIN" -m pip install --upgrade pip >/dev/null
"$PIPBIN" install \
  "neuroworkflow[pointnet,nest] @ git+https://github.com/oist/neuro-workflow.git@${NW_REF}" \
  jupyterlab
ok "neuroworkflow + bmtk + NEST wheel + jupyterlab installed"

# ---- 4. Verify the simulation stack imports --------------------------------
step "[4/5] Verifying the simulation stack"
"$PYBIN" - <<'PY'
from neuroworkflow import WorkflowBuilder
from neuroworkflow.nodes.network.NW_Population import NW_Population
import bmtk, nest, h5py, matplotlib  # noqa: F401
print("    neuroworkflow / bmtk / nest / h5py / matplotlib OK")
PY

# ---- 5. Download the PointNeuron notebooks (no clone) ----------------------
step "[5/5] Downloading PointNeuron notebooks into ./notebooks"
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
