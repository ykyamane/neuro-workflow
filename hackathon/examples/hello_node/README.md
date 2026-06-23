# hello_node — the 5-minute green run

A minimal, **dependency-free** NeuroWorkflow example (no NEST, no TVB — Python
stdlib only). Use it to confirm your environment works before pointing an agent
at your own code, and as a correct pattern for the agent to imitate.

## Files

| File | Role |
|------|------|
| `signal_generator.py` | A **source** node: generates a sine wave (no inputs). |
| `signal_statistics.py` | An **analysis** node: mean / std / count of a signal. |
| `workflow.py` | Wires the two nodes and runs them. |
| `EXPECTED_OUTPUT.md` | Golden numbers so you know the run actually worked. |

## Run it

```bash
# from this folder, with the venv active
python workflow.py
```

Compare the printed numbers to `EXPECTED_OUTPUT.md`.

## Then read the two nodes

They are the smallest complete examples of the node contract:

- the `NODE_DEFINITION` schema (`type`, `stage`, `tool`, `model_source`,
  `description`, `parameters`, `inputs`, `outputs`, `methods`);
- `add_process_step(...)` registering a method;
- a method returning a dict whose **keys equal the output port names** (the #1
  silent-failure trap — see the comment in `signal_generator.py`).

## Suggested session sequence (matches the team's onboarding plan)

1. Run `workflow.py` as-is → green run.
2. Change one parameter (e.g. `cycles=4.0` in `workflow.py`) and re-run.
3. Only then ask your agent to convert your own code in `source_code/`.
