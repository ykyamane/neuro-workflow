#!/usr/bin/env bash
#
# Hackathon starting-line setup for the NeuroWorkflow PointNeuron notebooks.
# Creates a conda/mamba environment with NEST (conda-forge) and
# neuroworkflow[pointnet] + bmtk (pip).
#
#   bash setup_hackathon.sh
#
# Re-runnable (idempotent): updates the env to match environment.yml.
set -euo pipefail

ENV_NAME="neuroworkflow-hackathon"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Detect a conda-family launcher: prefer mamba, then conda.
if command -v mamba >/dev/null 2>&1; then
  CONDA_EXE=mamba
elif command -v conda >/dev/null 2>&1; then
  CONDA_EXE=conda
else
  echo "==> No conda/mamba found."
  echo "    Install Miniforge (free, conda-forge default channel, bundles mamba):"
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64)  URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh" ;;
    Darwin-x86_64) URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh" ;;
    Linux-x86_64)  URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh" ;;
    Linux-aarch64) URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh" ;;
    *)             URL="https://github.com/conda-forge/miniforge#install" ;;
  esac
  echo
  echo "      curl -L -o Miniforge3.sh \"$URL\""
  echo "      bash Miniforge3.sh -b"
  echo "      ~/miniforge3/bin/conda init \"\$(basename \"\$SHELL\")\""
  echo
  echo "    Then restart your shell and re-run:  bash setup_hackathon.sh"
  exit 1
fi
echo "==> Using $CONDA_EXE"

# 2. Create or update the named env from environment.yml (idempotent).
if "$CONDA_EXE" env list | grep -qE "^[[:space:]]*${ENV_NAME}[[:space:]]"; then
  echo "==> Updating existing env '$ENV_NAME'"
  "$CONDA_EXE" env update -n "$ENV_NAME" -f environment.yml --prune
else
  echo "==> Creating env '$ENV_NAME'"
  "$CONDA_EXE" env create -n "$ENV_NAME" -f environment.yml
fi

# 3. Re-assert the editable install (covers source/extra edits on re-run).
#    `conda run` avoids depending on `conda activate` being shell-hooked.
echo "==> Installing neuroworkflow[pointnet] (editable)"
"$CONDA_EXE" run -n "$ENV_NAME" python -m pip install -e ".[pointnet]"

cat <<EOF

==> Done. Activate the environment and launch JupyterLab:

      conda activate ${ENV_NAME}
      cd notebooks
      jupyter lab

    Then Run All in any of:
      NW_SingleCell_PointNeuron.ipynb
      NW_Ring_PointNeuron.ipynb
      NW_BalancedNetwork_PointNeuron.ipynb
EOF
