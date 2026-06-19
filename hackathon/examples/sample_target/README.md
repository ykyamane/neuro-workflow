# sample_target — a stand-in for "your own code"

If you arrive without a suitable Python script (or just want a realistic warm-up),
use this. `lif_network.py` is an intentionally **unstructured** single-file script
— a leaky integrate-and-fire recurrent network with its parameters, simulation,
and analysis all mixed together — exactly the kind of code this hackathon converts
into nodes.

## Use it as your input

```bash
mkdir -p source_code
curl -fsSL https://raw.githubusercontent.com/oist/neuro-workflow/main/hackathon/examples/sample_target/lif_network.py \
  -o source_code/lif_network.py
python source_code/lif_network.py        # confirm it runs (prints a mean firing rate)
```

Then start your agent and run the `create-node` skill pointed at `source_code/`.

## What the agent should produce

A reasonable breakdown (the agent will propose its own and ask you to confirm):

- a **network** node — neuron count, connectivity, weights → a connectivity object;
- a **simulation** node — runs the LIF dynamics, records spike times;
- an **analysis** node — computes mean firing rate and a raster plot.

Wire them into a workflow and run it locally — the end-to-end result should match
the standalone script's printed firing rate.

> Requires only `numpy` (a core neuroworkflow dependency); the raster plot also uses
> `matplotlib`, which the hackathon setup installs.
