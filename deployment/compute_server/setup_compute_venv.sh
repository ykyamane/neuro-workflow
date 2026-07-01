#!/usr/bin/env bash
# One-time (idempotent) setup of the NeuroWorkflow runtime venv on the RIKEN
# compute server, used by the remote Slurm execution backend.
#
# Run this ON the compute server (login node), as the neuro-workflow user:
#   ssh neuro-workflow@digitalbrain.brainminds.jp
#   bash setup_compute_venv.sh                 # Phase 1: base (neuroworkflow + numpy)
#   WITH_NEST=1 bash setup_compute_venv.sh     # Phase 2: + [pointnet,nest] simulator stack
#
# No conda (RIKEN institutional licensing forbids it). Uses Environment Modules
# + a venv under /data/neuro-workflow/local, which is on the shared filesystem
# and therefore visible to every compute node.
#
# Note on the login node limits (4 GB RAM / 512 procs): wheel-based installs
# (numpy, the NEST PyPI wheel, neuroworkflow) are light and fine here. If a
# dependency has to build from source and gets killed, run this inside a small
# `sbatch` job on the ccalc partition instead.
set -euo pipefail

PREFIX="${PREFIX:-/data/neuro-workflow/local}"
VENV_DIR="${VENV_DIR:-$PREFIX/venv}"
PYTHON_MODULE="${PYTHON_MODULE:-python/3.11.14}"
NW_REF="${NW_REF:-main}"
WITH_NEST="${WITH_NEST:-0}"

echo "==> Loading Python module ($PYTHON_MODULE)"
if command -v module >/dev/null 2>&1; then
  module load "$PYTHON_MODULE" 2>/dev/null || \
    echo "    (module load failed; falling back to a python3.11/python3 on PATH)"
fi
PYBASE="$(command -v python3.11 || command -v python3)"
echo "    using $("$PYBASE" --version 2>&1) ($PYBASE)"

echo "==> Creating venv at $VENV_DIR"
mkdir -p "$PREFIX"
[ -x "$VENV_DIR/bin/python" ] || "$PYBASE" -m venv "$VENV_DIR"
PYBIN="$VENV_DIR/bin/python"
"$PYBIN" -m pip install --upgrade pip >/dev/null

if [ "$WITH_NEST" = "1" ]; then
  echo "==> Installing neuroworkflow[pointnet,nest] (NEST PyPI wheel + bmtk) @ $NW_REF"
  # pandas<2.3: BMTK breaks on pandas 3.0 StringDtype (matches the hackathon pin).
  "$VENV_DIR/bin/pip" install \
    "neuroworkflow[pointnet,nest] @ git+https://github.com/oist/neuro-workflow.git@${NW_REF}" \
    "pandas<2.3"
else
  echo "==> Installing neuroworkflow (base) + numpy @ $NW_REF"
  "$VENV_DIR/bin/pip" install \
    "git+https://github.com/oist/neuro-workflow.git@${NW_REF}" \
    numpy
fi

echo "==> Verifying import"
"$PYBIN" -c "from neuroworkflow.core.node import Node; import numpy; print('neuroworkflow + numpy OK')"
if [ "$WITH_NEST" = "1" ]; then
  "$PYBIN" -c "import nest, bmtk; print('NEST', nest.__version__, '+ bmtk OK')"
fi

echo "==> Done. The Slurm wrapper activates this venv automatically."
echo "    Manual activation: source $VENV_DIR/bin/activate"
