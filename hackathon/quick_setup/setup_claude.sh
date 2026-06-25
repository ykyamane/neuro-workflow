#!/usr/bin/env bash
#
# Hackathon one-command setup for the NeuroWorkflow + Claude Code environment.
#
#   Usage:   bash setup.sh
#
# Re-runnable (idempotent): safe to run multiple times. Creates a Python venv,
# installs a pinned neuro-workflow + Jupyter + matplotlib, lays out the project
# folders, and — most importantly — installs the Claude Code `create-node` Skill
# so that `/create-node` is available inside `claude`.
#
# This replaces the manual steps in hackaton_notes.txt and fixes their bugs:
#   * the skill never installed because `.claude/skills/create-node/` did not
#     exist before `curl -o` ran (curl does not create parent dirs);
#   * `claude init` is not a real subcommand — we generate CLAUDE.md here instead.
#
set -euo pipefail

# ---- Configuration ----------------------------------------------------------
VENV_DIR="${VENV_DIR:-venv}"                                   # python venv folder
PYTHON="${PYTHON:-python3}"                                    # base interpreter
# Pin neuro-workflow to a specific commit so every participant gets the SAME
# package AND the same Skill / guide. Bump this SHA to upgrade everyone at once.
NW_REF="${NW_REF:-main}"
RAW="https://raw.githubusercontent.com/oist/neuro-workflow/${NW_REF}"

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[0;32m✓ %s\033[0m\n' "$*"; }
trap 'printf "\n\033[1;31m✗ setup.sh failed (line %s). Re-run after fixing the error above.\033[0m\n" "$LINENO"' ERR

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

# ---- 5. Claude Code Skill + node-creation guide (THE key fix) ---------------
step "[5/7] Installing Claude Code skill: create-node"
SKILL_DIR=".claude/skills/create-node"
mkdir -p "$SKILL_DIR"                                          # <-- missing step that broke the notes
curl -fsSL --create-dirs -o "${SKILL_DIR}/SKILL.md" "${RAW}/.claude/skills/create-node/SKILL.md"
curl -fsSL -o "NODE_CREATION_GUIDE.md" "${RAW}/NODE_CREATION_GUIDE.md"
ok "downloaded SKILL.md and NODE_CREATION_GUIDE.md"

# ---- 6. Ensure the skill has frontmatter (reliable auto-invocation) --------
step "[6/7] Ensuring SKILL.md frontmatter"
if head -1 "${SKILL_DIR}/SKILL.md" | grep -q '^---'; then
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
    cat "${SKILL_DIR}/SKILL.md"
  } > "$tmp"
  mv "$tmp" "${SKILL_DIR}/SKILL.md"
  ok "prepended name/description frontmatter"
fi

# ---- 7. Starter CLAUDE.md (replaces the invalid `claude init`) --------------
step "[7/7] Project CLAUDE.md"
if [ -f "CLAUDE.md" ]; then
  ok "CLAUDE.md already exists — left unchanged"
else
  cat > CLAUDE.md <<'MD'
# NeuroWorkflow Hackathon Workspace

Workspace for building **NeuroWorkflow** simulation nodes during the hackathon.

## Environment
- Python venv lives in `./venv` (created by `setup.sh`). `neuroworkflow` is
  installed from a pinned commit, alongside `jupyterlab` and `matplotlib`.
- **fish shell:** activate with `source venv/bin/activate.fish`
  (bash/zsh: `source venv/bin/activate`). You can also call `venv/bin/python`
  and `venv/bin/jupyter lab` directly without activating.
- Re-run `bash setup.sh` any time to repair/refresh the environment.

## Layout
- `my_nodes/` — your custom NeuroWorkflow nodes go here.
- `source_code/` — scratch space / experiments / reference code.
- `NODE_CREATION_GUIDE.md` — conventions for stages, parameters, and ports.
- `.claude/skills/create-node/` — the Claude Code skill (see below).

## Creating nodes
Use the **`/create-node`** skill in Claude Code — type `/create-node` (or just
ask to "create a node") and follow the prompts. It generates a node class into
`my_nodes/` following `NODE_CREATION_GUIDE.md`. Key rules: give ports
scientifically-meaningful descriptions (units, populations), never call
`nest.ResetKernel()` at import/`__init__`, and make node names return-dict keys
match output port names.
MD
  ok "wrote starter CLAUDE.md"
fi

# ---- Done -------------------------------------------------------------------
step "Setup complete ✅"
cat <<EOF

Next steps:
  1. source ${VENV_DIR}/bin/activate  (bash/zsh)     # or: source ${VENV_DIR}/bin/activate.fish (fish)  
  2. Start Claude Code:   claude
  3. Press '/' and confirm '/create-node' appears  →  the Skill is loaded.
     Then run '/create-node' to scaffold a node into my_nodes/.

Optional: launch JupyterLab with  ${VENV_DIR}/bin/jupyter lab
EOF
