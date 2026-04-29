# Create NeuroWorkflow Node

Guide the user through creating a new node following the NODE_CREATION_GUIDE.md conventions, then generate the file.

Before starting, read `NODE_CREATION_GUIDE.md` to apply the current stage list and semantic guides. If the node will have multiple methods or is structurally complex, also browse `src/neuroworkflow/nodes/` for a comparable existing node to use as a reference.

---

## Step 0 — Audit existing nodes first

Before writing anything new, search `src/neuroworkflow/nodes/` to understand what already exists.

Ask yourself:

1. **Does an existing node already cover this?** If so, stop — point the user to it.
2. **Could an existing node be made configurable to cover both the old and new case?**
   - If yes, propose extending it with a `model_type`-style string parameter (see *Configurable node pattern* below) rather than creating a new node.
   - Only create a new node if the scientific interface (inputs/outputs) is meaningfully different, not just the parameters.
3. **Is a family of similar nodes being requested at once?** (e.g., from a notebook or paper)
   - Map all requested operations to candidate nodes first.
   - Identify which can share a single configurable node before deciding how many files to create.

When the source is a **Jupyter notebook** (.ipynb):
- Read the notebook cell by cell.
- Each coherent group of cells that produces a self-contained scientific object is a candidate node.
- Check existing nodes for each candidate before creating a new one.
- The notebook's parameter values become `default_value` in the node's `ParameterDefinition`.

---

## Step 1 — Gather requirements

Ask the user (all at once, in a single message) for the **required** fields. The optional fields below can be filled in later or inferred from the implementation — do not block on them.

### Required (always ask)

1. **Node name** — CamelCase class name (e.g. `NESTStriatumPopulationNode`)
2. **Stage** — determine the stage by reasoning from the node's role, not by matching against the list:
   - What does this node **consume**? (What must already exist for it to run?)
   - What does it **produce**? (What self-contained scientific object becomes available after it runs?)
   - Is that output something another node can consume without knowing how it was built?
   - Is this step conceptually independent from adjacent steps — i.e., could a different tool produce the same output and be swapped in?
   
   If yes to the last two, it is a distinct stage. Check `NODE_CREATION_GUIDE.md` to see if an existing stage matches. If no existing stage fits cleanly, propose a new one — a well-described new stage is better than a forced fit.
3. **Tool** — simulator or library (e.g. `NEST`, `TVB`, `Brian2`, `NEURON`, `SciPy`, `custom`)
4. **Model source** — URL to the GitHub repo, paper, or documentation this node implements
5. **Description** — one scientifically specific sentence (written for an AI agent to understand, not just a human)
6. **Parameters** — for each: `name`, `default_value`, `description`
7. **Inputs** — for each: `name`, `PortType`, description of the data
8. **Outputs** — for each: `name`, `PortType`, description of the data
9. **Methods** — processing method names, which inputs/outputs each uses, and what it does. If multiple methods are needed, list them in execution order (each method's outputs can be used as inputs to later methods).

Available PortTypes: `ANY`, `INT`, `FLOAT`, `STR`, `BOOL`, `LIST`, `DICT`, `OBJECT`, `FILE_PATH`, `CSV_FILE`, `JSON_FILE`, `PICKLE_FILE`, `NUMPY_FILE`, `HDF5_FILE`

### Optional / inferred (fill in when known)

- **Parameter constraints** (`min`/`max` or `allowed_values`) — add when the scientific meaning implies a valid range or a fixed set of options. Leave out if the range is open-ended or unknown.
- **Optimizable parameters** (`optimizable=True`, `optimization_range`) — add for parameters a researcher would tune or fit to data.
- **Objective parameters** (`is_objective=True`, `objective_range`) — add for output metrics that serve as optimization targets (e.g. mean firing rate, error).
- **Optional inputs** (`optional=True`) — always infer this from the code, do not ask. If the method uses the input unconditionally, the port is required (default). If the method signature has `= None` for that parameter, or the body guards it with `if input is None:`, mark the port `optional=True`. The rule: used unconditionally → required; guarded or defaulted to None → optional.

If the user provides existing code or a GitHub repo, extract as much of the optional metadata as possible from the implementation rather than asking for it.

---

## Configurable node pattern

When a family of related models exists (e.g. several TVB neural mass models, several NEST neuron types), prefer **one configurable node** over separate nodes per model.

**Use this pattern when:**
- Multiple models share the same scientific interface (same inputs/outputs/stage)
- The only differences are parameter values and which class gets instantiated
- Existing nodes cover one model and a new simulation adds another

**How to implement:**
- Add a `model_type` string parameter with `constraints={"allowed_values": [...]}` listing all supported classes.
- Add a `model_params` dict parameter for scalar constructor arguments (values become `np.array([v])` internally).
- Add a `region_params` dict parameter if per-region overrides are needed (e.g. epilepsy heatmaps).
- Make any input that is only needed for some configurations `optional=True`.
- Resolve the class at runtime via `getattr(module, model_type)` with a fallback for non-standard imports.

**Example (TVB model node):**
```python
"model_type": ParameterDefinition(
    default_value="Generic2dOscillator",
    description="TVB model class: 'Generic2dOscillator' (resting-state), 'EpileptorRestingState' (seizure/resting hybrid), ...",
    constraints={"allowed_values": ["Generic2dOscillator", "EpileptorRestingState", ...]},
),
"model_params": ParameterDefinition(
    default_value={"a": 1.74},
    description="Dict of scalar parameters passed to the model constructor as numpy arrays.",
),
```

This lets one node replace multiple model-specific nodes and serve both existing and new workflows by reconfiguring parameters.

---

## Step 2 — Handle new stage (if applicable)

If no existing stage fits, confirm the new stage name with the user before proceeding. A new stage is valid when:
- The operation is conceptually independent (different tool could produce the same output)
- It would apply to more than one possible node, not just this specific script
- A neuroscientist would describe it as a distinct step in the modeling process

Then:
1. Add the new stage entry to `NODE_CREATION_GUIDE.md` following the existing format (name, role, typical in/out, parameters, examples)
2. Create `src/neuroworkflow/nodes/<new_stage>/__init__.py`
3. Inform the user the new stage has been registered

---

## Step 3 — Generate the node file

### Where to place it

**New nodes always go to sandbox first:**
```
src/neuroworkflow/nodes/sandbox/<NodeName>.py
```

The sandbox is a staging area for nodes under development or not yet validated in a real workflow. Once the node has been tested end-to-end (smoke test + workflow execution), it can be promoted to its final stage folder:
```
src/neuroworkflow/nodes/<stage>/<NodeName>.py
```

Only place directly into a stage folder if the node is a straightforward extension of a well-understood existing node.

### File structure

```python
from typing import Dict, Any, Optional

# Domain-specific imports go here (e.g. import nest, from tvb.simulator import simulator)

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


class <NodeName>(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="<snake_case_type>",
        stage="<stage>",
        tool="<tool>",
        model_source="<url>",
        description="<one scientifically specific sentence written for an AI agent>",
        parameters={
            "<param>": ParameterDefinition(
                default_value=<default>,
                description="<specific description>",
                # constraints={"min": ..., "max": ...},  # or "allowed_values": [...]
                # optimizable=True,
                # optimization_range=[..., ...],
                # is_objective=True,
                # objective_range=[..., ...],
            ),
        },
        inputs={
            "<port>": PortDefinition(
                type=PortType.<TYPE>,
                description="<specific description of the data, not just the name>",
                # optional=True,  # add if this input is not required
            ),
        },
        outputs={
            "<port>": PortDefinition(
                type=PortType.<TYPE>,
                description="<specific description of the data, not just the name>",
            ),
        },
        methods={
            "<method>": MethodDefinition(
                description="<what this method computes>",
                inputs=["<port>", ...],
                outputs=["<port>", ...],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        # Add one call per method, in execution order.
        # For multi-step nodes, later methods can receive outputs of earlier ones via self._context.
        self.add_process_step("<method>", self.<method>, method_key="<method>")

    def <method>(self, <inputs>) -> Dict[str, Any]:
        # IMPORTANT: return dict keys must exactly match the output port names in NODE_DEFINITION.
        # A mismatch silently leaves the output port as None.
        # TODO: implement
        raise NotImplementedError
```

---

## Step 4 — Register the node

Add the import to `src/neuroworkflow/nodes/sandbox/__init__.py` (or the stage `__init__.py` if placing directly into a stage):

```python
from .<NodeName> import <NodeName>
```

---

## Step 5 — Run the checklist

Before finishing, verify every item:

- [ ] `stage` is set and matches the stage list
- [ ] `tool` identifies the simulator or library
- [ ] `model_source` URL is provided
- [ ] `description` is one clear scientific sentence written for an AI agent
- [ ] All parameters have `description` and `default_value`
- [ ] Parameters with numeric bounds have `constraints` (`min`/`max`)
- [ ] Parameters with fixed options have `constraints` (`allowed_values`)
- [ ] Scientifically tunable parameters have `optimizable=True` and `optimization_range`
- [ ] Optimization target metrics have `is_objective=True` and `objective_range`
- [ ] Optional input ports are marked `optional=True`
- [ ] All port descriptions are specific enough for an agent to understand the data
- [ ] Every method's return dict keys exactly match the corresponding output port names in `NODE_DEFINITION` (mismatch silently leaves ports as `None`)
- [ ] `type` field is globally unique across all nodes (check existing nodes — do not reuse a type string)
- [ ] Node is in `sandbox/` (or the correct stage folder if already validated)
- [ ] Import added to the corresponding `__init__.py`
- [ ] Smoke test: `from neuroworkflow.nodes.sandbox.<NodeName> import <NodeName>; n = <NodeName>("test"); print(n.get_info())`
- [ ] If configurable node pattern was used: verify all supported `model_type` values can be instantiated

---

## Step 6 — Tell the user

Report:
- File path created
- Checklist status
- Whether sandbox or stage folder was used, and what validation is needed before promotion
- If using the web app: sync to `gui/workflow_backend/django-project/codes/nodes/<stage>/` or rely on the Docker NODES_DIR mount

---

## Step 7 — Offer to create a companion workflow file

After one or more nodes are created and smoke-tested, offer to create a workflow `.py` file that wires them together and runs a simulation end-to-end.

A workflow file follows the pattern in `examples/epilepsy_rs.py`:

```python
from neuroworkflow import WorkflowBuilder
from neuroworkflow.nodes.sandbox.<NodeName> import <NodeName>

# 1. Instantiate nodes
node_a = NodeA("NodeA")
node_b = NodeB("NodeB")

# 2. Configure parameters
node_a.configure(param=value, ...)
node_b.configure(param=value, ...)

# 3. Build topology once
wf = WorkflowBuilder("WorkflowName")
wf.add_node(node_a)
wf.add_node(node_b)
wf.connect("NodeA", "output_port", "NodeB", "input_port")
workflow = wf.build()

# 4. Execute (reconfigure nodes between runs to vary parameters)
workflow.execute()

# 5. Reconfigure and re-execute for a second simulation variant
node_a.configure(param=other_value, ...)
workflow.execute()
```

**Key rules for workflow files:**
- Place in `src/neuroworkflow/nodes/sandbox/` while under development, or in `examples/` once validated.
- One `WorkflowBuilder` per topology. Re-execute the same `workflow` object after reconfiguring nodes — do not rebuild for parameter-only changes.
- Use descriptive node instance names (passed to the constructor) since these are used as keys in `connect()`.
- Build paths to data files with a try/except to handle both script and Jupyter notebook execution. Use the **same relative path in both branches** — `__file__` and `os.getcwd()` resolve to the same directory when the notebook CWD matches the script location:
  ```python
  try:
      _HERE = os.path.dirname(os.path.abspath(__file__))
  except NameError:
      _HERE = os.getcwd()  # Jupyter: CWD is typically the script's directory

  DATA_FILE = os.path.abspath(os.path.join(_HERE, "relative/path/to/data"))
  ```
