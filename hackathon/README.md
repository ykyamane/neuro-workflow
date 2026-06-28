# Theme 2 — Build NeuroWorkflow nodes from your own code

> Part of the **NeuroWorkflow Hackathon** kit. Start with
> [`PARTICIPANT_GUIDE.md`](./PARTICIPANT_GUIDE.md) for the overview, the core concepts, and
> Theme 1. **This file is the detailed step-by-step walkthrough for Theme 2.**

In Theme 2 you turn **your own Python code** into reusable **NeuroWorkflow nodes** and a
**workflow**, with an AI coding agent doing most of the heavy lifting. You then run it locally,
upload it to the NeuroWorkflow web app, and execute it on the server.

**No prior NeuroWorkflow experience is required.** The agent + the `create-node` skill guide
every step.

---

## Setup

From your own working folder, run the one-command script for your agent — keep the hackathon
kit as read-only reference (full details and a manual fallback are in [`SETUP.md`](./SETUP.md)):

```bash
# Claude Code:
bash /path/to/hackathon/quick_setup/setup_claude.sh
# Codex:
bash /path/to/hackathon/quick_setup/setup_codex.sh
```

This creates a Python virtual environment, installs NeuroWorkflow + JupyterLab + matplotlib,
makes a `source_code/` folder (drop your code here) and a `my_nodes/` folder (the agent writes
here), and installs the `create-node` skill for your agent.

**Sanity check — get a green run first.** Before using your own code, run the tiny
dependency-free example (no simulator) so you know the toolchain works and you can see what a
finished node looks like. With your venv active:

```bash
python /path/to/hackathon/examples/hello_node/workflow.py   # compare with EXPECTED_OUTPUT.md
```

(`SETUP.md` step C-2 also shows how to fetch this example straight into your working folder.)

---

## The agenda — four steps

You drive **steps 1–2** locally with your agent. Steps **3–4** happen in the web app.

### Step 1 — Local node building
- **No code to bring?** Use [`examples/sample_target/lif_network.py`](./examples/sample_target/) — a
  realistic, unstructured LIF-network script meant as a stand-in for your own code. Copy it into
  `source_code/` and proceed exactly as below.
- **What you do:** put your script in `source_code/`, start your agent, and run the `create-node` skill
  (Claude Code: `/create-node`; Codex: the `/skills` selector or `$create-node`). The agent reads your
  code, proposes a breakdown into nodes, **asks you to confirm**, then writes node files into `my_nodes/`.
- **What you get:** one or more NeuroWorkflow node `.py` files in `my_nodes/`, each with a clear schema
  (inputs, outputs, parameters) and your scientific logic inside.

### Step 2 — Local workflow & testing
- **What you do:** the agent wires your nodes into a workflow (`.py` + a Jupyter `.ipynb`) and runs it.
  Validate it: confirm the run succeeds and **no output is `None`**. Run
  `python check_node.py my_nodes/<NodeName>.py` on each node — it should print `ALL NODES PASSED`.
  Tweak a parameter or a connection and re-run to get a feel for the structure.
- **What you get:** a working workflow you have run end-to-end locally, with validated outputs — the proof
  that your nodes are correct and uploadable.
- **If your nodes need NEST/TVB and you can't install the simulator locally:** that's fine — local
  running is **optional**. The agent can still write the node files from your code, but you won't be able
  to *execute* them or run `check_node.py` on them locally (importing the node imports the simulator).
  In that case, do the real run **on the server (Step 4)**, where NEST and TVB are preinstalled. Pure
  Python / NumPy nodes (like `hello_node`) always run locally with no extra setup.

### Step 3 — Upload & reproduce in the GUI
- **What you do:** log in to the NeuroWorkflow web app and **upload each node `.py` file** under its
  category (`analysis`, `io`, `network`, `optimization`, `simulation`, `stimulus`). Rebuild your graph by
  dragging nodes from the palette and connecting them — or ask the **built-in AI assistant** to add and
  connect them (paste the node/edge summary your local agent printed).
- **What you get:** your workflow recreated visually in the platform, ready to run.

### Step 4 — Run on the server
- **What you do:** generate the workflow code in the GUI and run it.
- **What you get:** results collected in the app.
- **For this hackathon:** workflows run **directly on the application server**, so please keep example
  runs **lightweight** (short simulations, modest network sizes). A dedicated HPC compute backend is not
  used in this round.

---

For the file index, the core concepts, Theme 1, and support, see
[`PARTICIPANT_GUIDE.md`](./PARTICIPANT_GUIDE.md).
