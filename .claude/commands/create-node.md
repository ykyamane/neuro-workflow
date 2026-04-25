# Create NeuroWorkflow Node

Guide the user through creating a new node following the NODE_CREATION_GUIDE.md conventions, then generate the file.

Before starting, read `NODE_CREATION_GUIDE.md` to apply the current stage list and semantic guides.

## Step 1 — Gather requirements

Ask the user (all at once, in a single message):

1. **Node name** — CamelCase class name (e.g. `NESTStriatumPopulationNode`)
2. **Stage** — which brain modeling stage? (see NODE_CREATION_GUIDE.md stage list). If the model does not fit any existing stage cleanly, propose a new stage name and a one-paragraph description — the skill will add it to NODE_CREATION_GUIDE.md and create the folder.
3. **Tool** — simulator or library (e.g. `NEST`, `TVB`, `Brian2`, `NEURON`, `SciPy`, `custom`)
4. **Model source** — URL to the GitHub repo, paper, or documentation this node implements
5. **Description** — one scientifically specific sentence (written for an AI agent to understand)
6. **Parameters** — for each: `name`, `default_value`, `description`, whether it is `optimizable` and its `optimization_range`
7. **Inputs** — for each: `name`, `PortType`, and a specific description of the data
8. **Outputs** — for each: `name`, `PortType`, and a specific description of the data
9. **Methods** — processing method names, which inputs/outputs each uses, and what it does

Available PortTypes: `ANY`, `INT`, `FLOAT`, `STR`, `BOOL`, `LIST`, `DICT`, `OBJECT`, `FILE_PATH`, `CSV_FILE`, `JSON_FILE`, `PICKLE_FILE`, `NUMPY_FILE`, `HDF5_FILE`

## Step 2 — Handle new stage (if applicable)

If the user proposed a new stage:
1. Add the new stage entry to `NODE_CREATION_GUIDE.md` following the existing format (name, role, typical in/out, parameters, examples)
2. Create `src/neuroworkflow/nodes/<new_stage>/__init__.py`
3. Inform the user the new stage has been registered

## Step 3 — Generate the node file

Place the file at:
```
src/neuroworkflow/nodes/<stage>/<NodeName>.py
```

Use this structure:

```python
from typing import Dict, Any, Optional

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
        description="<one scientifically specific sentence>",
        parameters={
            "<param>": ParameterDefinition(
                default_value=<default>,
                description="<specific description>",
                # constraints={"min": ..., "max": ...},
                # optimizable=True,
                # optimization_range=[..., ...],
            ),
        },
        inputs={
            "<port>": PortDefinition(
                type=PortType.<TYPE>,
                description="<specific description of the data, not just the name>",
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
        self.add_process_step("<method>", self.<method>, method_key="<method>")

    def <method>(self, <inputs>) -> Dict[str, Any]:
        # TODO: implement
        raise NotImplementedError
```

## Step 4 — Register the node

Add the import to the stage folder's `__init__.py`:

```python
from .<NodeName> import <NodeName>
```

## Step 5 — Run the checklist

Before finishing, verify every item from the NODE_CREATION_GUIDE.md checklist:

- [ ] `stage` is set and matches the stage list
- [ ] `tool` identifies the simulator or library
- [ ] `model_source` URL is provided
- [ ] `description` is one clear scientific sentence
- [ ] All parameters have `description` and `default_value`
- [ ] Scientifically tunable parameters have `optimizable=True` and `optimization_range`
- [ ] All port descriptions are specific enough for an agent to understand the data
- [ ] Node is in the correct `src/neuroworkflow/nodes/<stage>/` folder
- [ ] Import added to the stage `__init__.py`

## Step 6 — Tell the user

Report:
- File path created
- Checklist status
- If using the web app: sync to `gui/workflow_backend/django-project/codes/nodes/<stage>/` or rely on the Docker NODES_DIR mount
