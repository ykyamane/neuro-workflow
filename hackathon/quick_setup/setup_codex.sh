#!/usr/bin/env bash
#
# Hackathon one-command setup for the NeuroWorkflow + Codex CLI environment.
#
#   Usage:   bash setup_codex.sh
#
# Codex CLI version of setup.sh. Re-runnable (idempotent): creates a Python venv,
# installs a pinned neuro-workflow + Jupyter + matplotlib, lays out the project
# folders, and installs the `create-node` Agent Skill so that it is available in
# `codex` via the /skills selector or a `$create-node` mention.
#
# Differences from the Claude Code setup.sh:
#   * the skill is installed under .codex/skills/create-node/ (Codex scans this
#     project-local path; the Claude version used .claude/skills/create-node/);
#   * Codex REQUIRES YAML frontmatter (name + description) in SKILL.md — the
#     upstream file has none, so we always prepend it here;
#   * project context is written to AGENTS.md (Codex's instruction file), the
#     analogue of CLAUDE.md.
#
set -euo pipefail

# ---- Configuration ----------------------------------------------------------
VENV_DIR="${VENV_DIR:-venv}"                                   # python venv folder
PYTHON="${PYTHON:-python3}"                                    # base interpreter
# Pin neuro-workflow so every participant gets the SAME package AND Skill / guide.
# Bump this ref (a commit SHA or branch) to upgrade everyone at once.
NW_REF="${NW_REF:-main}"
RAW="https://raw.githubusercontent.com/oist/neuro-workflow/${NW_REF}"
# Project-local skill dir (Codex Project scope). Override to put it user-global:
#   CODEX_SKILL_DIR=~/.codex/skills/create-node bash setup_codex.sh
CODEX_SKILL_DIR="${CODEX_SKILL_DIR:-.codex/skills/create-node}"

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[0;32m✓ %s\033[0m\n' "$*"; }
trap 'printf "\n\033[1;31m✗ setup_codex.sh failed (line %s). Re-run after fixing the error above.\033[0m\n" "$LINENO"' ERR

# ---- 1. Python virtual environment -----------------------------------------
step "[1/7] Python virtual environment (./${VENV_DIR})"
if [ ! -x "${VENV_DIR}/bin/python" ]; then
  "$PYTHON" -m venv "$VENV_DIR"
  ok "created venv with $("$PYTHON" --version 2>&1)"
else
  ok "reusing existing venv ($("${VENV_DIR}/bin/python" --version 2>&1))"
fi
PYBIN="${VENV_DIR}/bin/python"        # call these directly — no activate needed,
PIPBIN="${VENV_DIR}/bin/pip"          # so this works regardless of fish/bash/zsh.

# ---- 2. Dependencies (pinned) ----------------------------------------------
step "[2/7] Installing dependencies (pinned to ${NW_REF:0:12})"
"$PYBIN" -m pip install --upgrade pip >/dev/null
"$PIPBIN" install \
  "git+https://github.com/oist/neuro-workflow.git@${NW_REF}" \
  jupyterlab \
  matplotlib
ok "neuro-workflow @ ${NW_REF:0:12}, jupyterlab, matplotlib installed"

# ---- 3. Verify the package imports -----------------------------------------
step "[3/7] Verifying neuroworkflow import"
"$PYBIN" -c "from neuroworkflow.core.node import Node; print('    neuroworkflow OK')"

# ---- 4. Project folders -----------------------------------------------------
step "[4/7] Project folders"
mkdir -p source_code my_nodes
ok "source_code/ and my_nodes/ ready"

# ---- 5. Codex Agent Skill + node-creation guide -----------------------------
step "[5/7] Installing Codex skill: create-node -> ${CODEX_SKILL_DIR}"
mkdir -p "$CODEX_SKILL_DIR"
curl -fsSL --create-dirs -o "${CODEX_SKILL_DIR}/SKILL.md" "${RAW}/.claude/skills/create-node/SKILL.md"
curl -fsSL -o "NODE_CREATION_GUIDE.md" "${RAW}/NODE_CREATION_GUIDE.md"
ok "downloaded SKILL.md and NODE_CREATION_GUIDE.md"

# ---- 6. Ensure SKILL.md frontmatter (REQUIRED by Codex) ---------------------
step "[6/7] Ensuring SKILL.md frontmatter (required by Codex)"
if head -1 "${CODEX_SKILL_DIR}/SKILL.md" | grep -q '^---'; then
  ok "frontmatter already present"
else
  tmp="$(mktemp)"
  {
    cat <<'FM'
---
name: create-node
description: Create a new NeuroWorkflow node (NEST / TVB / Brian2 / custom computation) following the NODE_CREATION_GUIDE.md conventions, then generate the file. Use when the user wants to build or add a workflow node.
---

FM
    cat "${CODEX_SKILL_DIR}/SKILL.md"
  } > "$tmp"
  mv "$tmp" "${CODEX_SKILL_DIR}/SKILL.md"
  ok "prepended name/description frontmatter"
fi

# ---- 7. Starter AGENTS.md (Codex's project instruction file) ----------------
step "[7/7] Project AGENTS.md"
if [ -f "AGENTS.md" ]; then
  ok "AGENTS.md already exists — left unchanged"
else
  cat > AGENTS.md <<'MD'
# NeuroWorkflow Hackathon Workspace

Workspace for building **NeuroWorkflow** simulation nodes during the hackathon.

## Environment
- Python venv lives in `./venv` (created by `setup_codex.sh`). `neuroworkflow` is
  installed from a pinned ref, alongside `jupyterlab` and `matplotlib`.
- **fish shell:** activate with `source venv/bin/activate.fish`
  (bash/zsh: `source venv/bin/activate`). You can also call `venv/bin/python`
  and `venv/bin/jupyter lab` directly without activating.
- Re-run `bash setup_codex.sh` any time to repair/refresh the environment.

## Layout
- `my_nodes/` — your custom NeuroWorkflow nodes go here.
- `source_code/` — scratch space / experiments / reference code.
- `NODE_CREATION_GUIDE.md` — conventions for stages, parameters, and ports.
- `.codex/skills/create-node/` — the Codex Agent Skill (see below).

## Creating nodes
Use the **create-node** skill: in `codex`, open the `/skills` selector or type
`$create-node` (Codex may also trigger it implicitly when you ask to "create a
node"). It generates a node class into `my_nodes/` following
`NODE_CREATION_GUIDE.md`. Key rules: give ports scientifically-meaningful
descriptions (units, populations), never call `nest.ResetKernel()` at
import/`__init__`, and make each method's return-dict keys match its output
port names.
MD
  ok "wrote starter AGENTS.md"
fi

# ---- Done -------------------------------------------------------------------
step "Setup complete ✅"
cat <<EOF

Next steps:
  1. source ${VENV_DIR}/bin/activate  (bash/zsh)     # or: source ${VENV_DIR}/bin/activate.fish (fish)
  2. Start Codex:   codex
  3. Open the '/skills' selector (or type '\$create-node') and confirm
     'create-node' is listed  →  the Skill is loaded.
     Then run it to scaffold a node into my_nodes/.

Skill installed at: ${CODEX_SKILL_DIR}/SKILL.md
Optional: launch JupyterLab with  ${VENV_DIR}/bin/jupyter lab
EOF
