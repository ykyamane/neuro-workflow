"""Minimal two-node workflow: SignalGenerator -> SignalStatistics.

Run it to get a guaranteed green run (no simulator required):

    python workflow.py

Then compare the printed values to EXPECTED_OUTPUT.md.
"""

import os
import sys

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()  # Jupyter: CWD is typically the script's directory

# Make the node files importable in standalone mode (mirrors how participants
# keep their nodes next to the workflow in my_nodes/).
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from neuroworkflow import WorkflowBuilder
from signal_generator import SignalGeneratorNode
from signal_statistics import SignalStatisticsNode

# 1. Instantiate nodes (the constructor name is the key used in connect()).
generator = SignalGeneratorNode("Generator")
statistics = SignalStatisticsNode("Stats")

# 2. Configure parameters.
generator.configure(length=100, amplitude=1.0, cycles=2.0)

# 3. Build the topology once.
wf = WorkflowBuilder("HelloNodeWorkflow")
wf.add_node(generator)
wf.add_node(statistics)
wf.connect("Generator", "signal", "Stats", "signal")
workflow = wf.build()

# 4. Execute.
success = workflow.execute()

print("\n--- results ---")
print("workflow success:", success)
print("mean:      ", statistics.get_output("mean"))
print("std:       ", statistics.get_output("std"))
print("n_samples: ", statistics.get_output("n_samples"))
