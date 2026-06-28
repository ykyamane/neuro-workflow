# NeuroWorkflow Hackathon — Participant Setup

> **Fastest path — use the official one-command script for your agent.** Run it from **your
> own working folder** (keep the hackathon kit as read-only reference):
>
> ```bash
> # Claude Code:
> bash /path/to/hackathon/quick_setup/setup_claude.sh
> # Codex:
> bash /path/to/hackathon/quick_setup/setup_codex.sh
> ```
>
> Each script is idempotent and does everything below automatically: creates the venv, installs a
> **pinned** neuroworkflow + JupyterLab + matplotlib, makes `source_code/` and `my_nodes/`, installs the
> `create-node` skill into the right path for your agent (`.claude/skills/` or `.codex/skills/`) **with
> frontmatter**, and writes a starter `CLAUDE.md` / `AGENTS.md`.
>
> The manual steps below are the **explanation / fallback** if you are not using the scripts.

---

Two tracks: **Claude Code** and **Codex**. Steps A–C are identical for both; step D differs.

> The `curl` commands below pull from the raw-GitHub base
> `https://raw.githubusercontent.com/oist/neuro-workflow/main`. (Organizers may give you a specific commit
> SHA in place of `main` so everyone runs the exact same version.)

---

## A. Create an isolated environment

```bash
python3 -m venv neuro-env
source neuro-env/bin/activate          # Windows: neuro-env\Scripts\activate
```

## B. Install NeuroWorkflow + notebook tools

```bash
pip install --upgrade pip
pip install "git+https://github.com/oist/neuro-workflow.git"
pip install jupyterlab matplotlib
```

> **Simulators (NEST/TVB) are NOT installed by the line above.** If your code needs them, install them
> separately and ideally via conda (NEST rarely installs cleanly through pip). Ask an organizer if your
> install fails — do not burn time fighting it. A pure-Python / NumPy / Brian2 example always works.
> **Local execution of NEST/TVB nodes is optional:** the authoritative run happens in the GUI on the
> server, where NEST and TVB are preinstalled. If you can't install them locally, build the nodes anyway
> and run them on the server.

## C. Verify the install and make the working folders

```bash
python3 -c "from neuroworkflow.core.node import Node; print('OK')"

mkdir -p source_code      # put your existing (unstructured) Python code here
mkdir -p my_nodes         # the agent will write nodes + workflows here
```

## C-2. Get a green run first (recommended)

Before pointing an agent at your own code, confirm the toolchain works with a tiny, dependency-free
example (no NEST/TVB). This also gives the agent a correct pattern to imitate.

```bash
mkdir -p hello_node
base=https://raw.githubusercontent.com/oist/neuro-workflow/main/hackathon
curl -fsSL $base/check_node.py                          -o check_node.py
curl -fsSL $base/examples/hello_node/signal_generator.py  -o hello_node/signal_generator.py
curl -fsSL $base/examples/hello_node/signal_statistics.py -o hello_node/signal_statistics.py
curl -fsSL $base/examples/hello_node/workflow.py          -o hello_node/workflow.py
curl -fsSL $base/examples/hello_node/EXPECTED_OUTPUT.md   -o hello_node/EXPECTED_OUTPUT.md

cd hello_node && python workflow.py        # compare the numbers to EXPECTED_OUTPUT.md
cd .. && python check_node.py hello_node/signal_generator.py   # should end with ALL NODES PASSED
```

`check_node.py` is a deterministic validator: it instantiates a node, checks that every method output
maps to a declared port, and (when the node has no required inputs) runs one step and confirms no output
came back `None`. Use it on the agent's nodes too — it catches the silent-failure traps the engine hides.

---

## D-1. Claude Code track (preferred)

Download the skill (folder form with `SKILL.md`), the node guide, and the canonical instruction file:

```bash
mkdir -p .claude/skills/create-node
curl -fsSL https://raw.githubusercontent.com/oist/neuro-workflow/main/.claude/skills/create-node/SKILL.md -o .claude/skills/create-node/SKILL.md
curl -fsSL https://raw.githubusercontent.com/oist/neuro-workflow/main/NODE_CREATION_GUIDE.md             -o NODE_CREATION_GUIDE.md
curl -fsSL https://raw.githubusercontent.com/oist/neuro-workflow/main/hackathon/CLAUDE.md                -o CLAUDE.md
```

Start Claude Code in this folder, then give it this prompt:

```
Use the /create-node skill. Look in the source_code/ folder, find the main Python file(s),
analyze the code, and propose the nodes to build. Ask me to confirm the breakdown before you
write anything. Save the nodes AND two workflow files (.py and .ipynb) in the my_nodes/ folder.
Then smoke-test each node and run the workflow so we can see the outputs.
```

(`claude init` is optional — it only generates a thin starter `CLAUDE.md`. The curled `CLAUDE.md` and the
skill already contain the real instructions, so you can skip `init` or let it run; it won't hurt.)

---

## D-2. Codex track

Codex scans `.codex/skills/` (not `.claude/skills/`) and reads `AGENTS.md` as its project instruction
file. It has **no `/create-node` command** — a skill is triggered via the `/skills` selector or a
`$create-node` mention. Install the skill under the Codex path, the canonical `AGENTS.md`, and the guide:

```bash
mkdir -p .codex/skills/create-node
curl -fsSL https://raw.githubusercontent.com/oist/neuro-workflow/main/.claude/skills/create-node/SKILL.md -o .codex/skills/create-node/SKILL.md
curl -fsSL https://raw.githubusercontent.com/oist/neuro-workflow/main/hackathon/AGENTS.md                 -o AGENTS.md
curl -fsSL https://raw.githubusercontent.com/oist/neuro-workflow/main/NODE_CREATION_GUIDE.md              -o NODE_CREATION_GUIDE.md
```

> **Codex requires YAML frontmatter** (`name` + `description`) at the top of `SKILL.md`. The repo
> `SKILL.md` now ships with this block, so the `curl` above is enough. Only if you pull an older ref that
> lacks it, prepend (the official `setup_codex.sh` also does this automatically):
>
> ```
> ---
> name: create-node
> description: Create a new NeuroWorkflow node (NEST / TVB / Brian2 / custom computation) following the NODE_CREATION_GUIDE.md conventions, then generate the file. Use when the user wants to build or add a workflow node.
> ---
> ```

If you don't have a Codex/OpenAI subscription, set the API key the organizers gave you:

```bash
export OPENAI_API_KEY=sk-...     # organizer-provided; suggested model: gpt-4o-mini or better
```

Start Codex in this folder, then give it this prompt (trigger the skill via `/skills` or `$create-node`;
`AGENTS.md` also carries the rules as a fallback):

```
Use the create-node skill ($create-node). Look in the source_code/ folder, find the main Python
file(s), analyze the code, and propose the nodes to build. Ask me to confirm the breakdown before
you write anything. Save the nodes AND two workflow files (.py and .ipynb) in the my_nodes/ folder.
Then smoke-test each node and run the workflow so we can see the outputs.
```

---

## After the agent finishes (both tracks)

1. Open `my_nodes/` and run the generated `.ipynb` in JupyterLab (`jupyter lab`) to confirm it works
   locally and the outputs are not `None`. Also run `python check_node.py my_nodes/<NodeName>.py` on each
   generated node — it should end with `ALL NODES PASSED`.
2. Tweak a parameter or a connection and re-run to get a feel for the node structure.
3. Log in to the NeuroWorkflow web app and **upload each node `.py` file** under its category
   (`analysis`, `io`, `network`, `optimization`, `simulation`, `stimulus`).
4. Rebuild the graph: drag the nodes from the palette and connect them, OR ask the in-app AI assistant to
   add and connect them (paste the node/edge summary the agent printed).
5. Generate code and run on the server.
