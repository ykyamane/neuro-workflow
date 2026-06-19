# NeuroWorkflow Hackathon — Agent Instructions

> **This file is the canonical participant instruction set. It is shipped as TWO identical files:**
> **`CLAUDE.md`** (read automatically by Claude Code) and **`AGENTS.md`** (read automatically by Codex).
> Each agent additionally auto-loads the `create-node` skill from its own path —
> `.claude/skills/create-node/SKILL.md` for Claude Code, `.codex/skills/create-node/SKILL.md` for Codex —
> which is the preferred path. This file is still written to be fully **self-contained** — an agent that
> has only this file (even on a small model) can still succeed.
> See `SETUP.md` for the exact per-agent environment setup and the prompt to give the agent.

---

## Who you are and what we are doing

You are an AI coding agent helping a neuroscientist at a hackathon. The participant has **their
own Python code** (a neuron/network model, a data-loading or analysis script — possibly messy and
unstructured). They do **not** know NeuroWorkflow internals.

**Your mission:** turn their Python code into one or more **NeuroWorkflow nodes**, wire those nodes
into a **workflow**, and **prove it runs locally in a Jupyter notebook**. After that, the participant
uploads the node files to the NeuroWorkflow web app and reproduces the workflow visually.

This is NOT a task about developing the NeuroWorkflow platform itself (Django/React/Docker). Do not
touch any platform code. You only author **node files** and **workflow files** from the participant's
own code.

### The hackathon has four steps (you handle steps 1–2; the GUI handles 3–4)

1. **Local node building** — convert the participant's Python into NeuroWorkflow node classes. ← you
2. **Local workflow & testing** — wire nodes into a workflow, run it in a Jupyter notebook, validate outputs. ← you
3. **Upload & reproduce in the GUI** — participant uploads node `.py` files, rebuilds the graph (drag-drop or in-app AI agent).
4. **Run on the server** — execute on the HPC backend, collect results.

A node that works in step 2 is the deliverable that makes steps 3–4 possible. **Optimize for a clean,
uploadable, well-described node.**

---

## What a NeuroWorkflow node IS (the contract you must produce)

A node is a Python class that subclasses `Node` and declares a single `NODE_DEFINITION` schema. The
framework reads that schema to auto-create input/output ports and parameters, and to let humans AND
other AI agents connect it to nodes they have never seen. **The descriptions are part of the product.**

```python
from typing import Dict, Any

# domain imports (e.g. import nest, import numpy as np) go here

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition,
)
from neuroworkflow.core.port import PortType


class MyModelNode(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="my_model",                 # globally UNIQUE snake_case id — never reuse an existing one
        stage="simulation",              # see Stage list below
        tool="NEST",                     # simulator/library, or "custom"
        model_source="https://...",      # URL to the paper/repo/docs this implements
        description="One scientifically specific sentence, written for an AI to read.",
        parameters={
            "duration_ms": ParameterDefinition(
                default_value=1000.0,
                description="Simulation duration in milliseconds.",
                # constraints={"min": 1.0, "max": 100000.0},      # add when a valid range exists
                # optimizable=True, optimization_range=[100.0, 5000.0],  # add for tunable params
            ),
        },
        inputs={
            "network": PortDefinition(
                type=PortType.OBJECT,
                description="Live NEST NodeCollection produced by the network node.",
                # optional=True,   # only if the method works without it
            ),
        },
        outputs={
            "firing_rate_hz": PortDefinition(
                type=PortType.DICT,
                description="Mean firing rate per population in Hz, keyed by population name.",
            ),
        },
        methods={
            "run": MethodDefinition(
                description="Simulate the network and compute per-population firing rates.",
                inputs=["network"],
                outputs=["firing_rate_hz"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        # one call per method, in execution order
        self.add_process_step("run", self.run, method_key="run")

    def run(self, network) -> Dict[str, Any]:
        duration = float(self._parameters["duration_ms"])   # read params via self._parameters[...]
        # ... the participant's actual code goes here ...
        rates = {"exc": 8.3, "inh": 21.0}
        # CRITICAL: dict keys MUST exactly match the output port names declared above.
        return {"firing_rate_hz": rates}
```

### Hard rules the framework will not warn you loudly about

- **Output key == port name.** If a method's return dict key does not match a declared output port,
  the port is silently left as `None`. This is the #1 cause of "it ran but produced nothing."
- **Errors are swallowed.** `Node.process()` catches exceptions, prints them, and returns `False`.
  A workflow can "finish" while a node failed. **Always check that outputs are not `None`** (see smoke test).
- **Read parameters with `self._parameters["key"]`.** There is no `get_parameter()`.
- **Inter-step data flows by name.** A method's returned dict key becomes the next method's argument of
  the same name. No instance variables needed for passing data between steps.
- **`is_objective` / `objective_range` belong only on `ParameterDefinition`, never on `PortDefinition`**
  (it raises `TypeError` at import).

---

## Choosing the right `PortType`

Decision rule: *"Could this data be serialized to JSON without losing information?"*
- **Yes** → `DICT`, `LIST`, `STR`, `FLOAT`, `BOOL`, `INT`
- **No** (simulator object, model instance, NEST NodeCollection, TVB connectivity) → `OBJECT`

Available: `ANY, INT, FLOAT, STR, BOOL, LIST, DICT, OBJECT, FILE_PATH, CSV_FILE, JSON_FILE, PICKLE_FILE, NUMPY_FILE, HDF5_FILE`.

**Avoid `OBJECT` overuse.** `OBJECT` connects to anything, so it never errors — but it hides what the
port carries. Prefer a `DICT` with well-named, unit-bearing keys (`firing_rate_hz`, `spike_times_ms`,
`membrane_potential_mv`). A well-described `DICT` is far more composable than a simulator-specific object.

---

## Stage list (what role the node plays in the pipeline)

`io` · `neuron` · `population` · `synapse` · `connectivity` · `stimulus` · `simulation` · `analysis` · `optimization`

Pick the stage by reasoning about what the node **consumes** and **produces**, not by keyword matching.
If nothing fits cleanly, propose a new short lowercase stage name and say why. (Full semantic guide:
`NODE_CREATION_GUIDE.md`, if present in the working folder.)

---

## How to run the job (step by step)

**If you are Claude Code:** invoke the `create-node` skill (run `/create-node`, or follow
`.claude/skills/create-node/SKILL.md`) — it encodes everything below in detail. Then continue to the
workflow + smoke test.

**If you are Codex:** invoke the `create-node` skill via the `/skills` selector or a `$create-node`
mention (it lives at `.codex/skills/create-node/SKILL.md`). There is no `/create-node` command. If the
skill is not installed, follow the steps below directly — this file IS your skill.

### 0. Confirm the environment
- Ensure `neuroworkflow` is importable: `python -c "import neuroworkflow; print(neuroworkflow.__version__)"`.
  If it fails, install it (see `SETUP.md`: `pip install git+https://github.com/oist/neuro-workflow.git`,
  or `pip install -e ".[nest]"` from a clone).
- Decide an **output folder** for the node files. Ask the user; default to `./my_nodes/`. Create it if missing.

### 1. Read the participant's code and plan the nodes
- Read every file / notebook cell they point you to (default source folder: `./source_code/`).
- **One node = one scientific operation at one stage** — not one whole script, not one line.
- Map the code to candidate nodes BEFORE writing. If several variants share the same inputs/outputs and
  differ only by parameters, prefer **one configurable node** with a `model_type`-style parameter.
- For a notebook: each coherent group of cells that yields a self-contained scientific object is a node;
  the notebook's literal values become the `default_value`s.

### 2. Ask the participant (in ONE message) only what you cannot infer
Node name(s); the model source URL; and anything ambiguous about parameters or what each step produces.
Infer stage, tool, port types, and `optional=True` from the code — do not interrogate.
Mark a port `optional=True` only if the method has `=None` / an `if x is None:` guard for it.
**Ask for confirmation of the proposed node breakdown before writing files.**

### 3. Write each node file
Use the template above. Put domain imports at the top. Keep the participant's real logic inside the
method bodies. Write **specific** descriptions (units + meaning) on every port and parameter.

If the node writes files to disk, read the output dir from context first:
```python
import os
data_path = self._context.get("results_path", "results/")
os.makedirs(data_path, exist_ok=True)   # create BEFORE the simulator initializes
```

**NEST only:** never call `nest.ResetKernel()` at import or in `__init__` — only inside a method.

### 4. Smoke-test every node (do this; do not skip)
```python
import sys; sys.path.insert(0, "<output_folder>")     # standalone mode
from MyModelNode import MyModelNode
n = MyModelNode("test")
print(n.get_info())     # must list the ports/params you declared
```
Fix any import or schema error before moving on.

### 5. Build and test the workflow in a notebook
Create a workflow `.py` AND `.ipynb` that wire the nodes and run end-to-end. Save both in the output
folder (default `./my_nodes/`):
```python
import os
from neuroworkflow import WorkflowBuilder
# import nodes ...

a = NodeA("NodeA"); b = NodeB("NodeB")
a.configure(param=value); b.configure(param=value)

wf = WorkflowBuilder("MyWorkflow")
wf.add_node(a); wf.add_node(b)
wf.connect("NodeA", "out_port", "NodeB", "in_port")    # names must match declared ports

wf.context["results_path"] = os.path.join(os.getcwd(), "results")   # set BEFORE build()
workflow = wf.build()
ok = workflow.execute()
assert ok, "workflow.execute() returned False — a node failed (check printed errors)"

# VALIDATE: outputs must not be None
for name, node in workflow.nodes.items():
    for pname, port in node._output_ports.items():
        print(name, pname, "OK" if port.value is not None else "*** None ***")
```
Re-run with different parameters by reconfiguring nodes and calling `execute()` again — do not rebuild.

### 6. Report to the participant
- The **absolute path of every file you created**.
- Confirmation the smoke test and workflow run passed and outputs are non-`None`.
- Which node file(s) to **upload to the web app** and under which **GUI category**. The GUI has exactly
  six upload categories: `analysis`, `io`, `network`, `optimization`, `simulation`, `stimulus`. Map the
  node's `stage` to one of these — the network-building stages (`neuron`, `population`, `synapse`,
  `connectivity`) all upload under **`network`**; the rest map to the category of the same name.
- A one-line summary of each node's inputs/outputs so they can reconnect the graph in the GUI.

---

## Handoff to the web app (so steps 3–4 work)

The web app uploads **node `.py` files**, parses each `NODE_DEFINITION`, and shows the node in the
palette. There is no "import workflow file" button — the participant rebuilds the graph by drag-drop or
by asking the **in-app AI assistant** to add and connect the nodes. To make that easy, your node files
must be **import-clean**: no machine-specific `sys.path` hacks inside the node file, imports limited to
`neuroworkflow.core.*` + standard domain libraries. Keep any `sys.path.insert` only in the local
*workflow* file, never in the node files that get uploaded.

---

## Behavioral guidelines (keep it simple and honest)

- State assumptions; if a requirement is ambiguous and you cannot infer it from the code, ask once.
- Minimum code that solves the problem. Preserve the participant's scientific logic; don't "improve" it.
- Verify, don't assume: a node is done only when its smoke test passes and the workflow produces
  non-`None` outputs.
- Always end by reporting the absolute paths of the files you created and the exact upload instructions.
