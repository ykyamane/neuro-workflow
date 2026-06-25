NeuroWorkflow Hackathon — Participant Guide


1. Introduction to Neuro-Workflow and the NW Model Builder

Neuro-Workflow is a node-based model builder for computational neuroscience. A model is
expressed as a graph of reusable components:

  - A node is a Python class that wraps one scientific operation (build a population, add
    connectivity, run a simulation, compute firing rates). Each node declares its inputs,
    outputs, and parameters through a schema, so it can be connected to other nodes — even
    nodes written by other teams or for other simulators.
  - A workflow is a graph of connected nodes. Running it executes the nodes in order and
    passes data along the connections.

The same model can be built and run in two places: locally through the Neuro-Workflow Python
API (in a Jupyter notebook), and visually in the web application (GUI) on the server.

In this theme you will learn Neuro-Workflow using a set of example workflows built with the
NW Model Builder nodes (population, connectivity, stimulus, simulation, analysis).

Setup — prepare your environment before the hackathon

  Do these steps beforehand so you arrive ready to run. The three example workflows use the
  NEST simulator (with BMTK), so they go in the same virtual environment as Neuro-Workflow.
  This uses a plain Python venv, the same kind the Theme 2 setup scripts create.

    1) Create a folder for this theme and move into it:

         mkdir nw_notebooks
         cd nw_notebooks

    2) Create and activate a virtual environment:

         python3 -m venv venv
         source venv/bin/activate          # Windows: venv\Scripts\activate

    3) Install NEST into this virtual environment. NEST (version 3.7 or newer) must be
       available in the same venv. NEST can be difficult to install and the procedure depends
       on your system, so follow the official NEST installation instructions; conda is often
       the most reliable route (conda install -c conda-forge nest-simulator). If it does not
       install locally, you can still do Activity 2 on the server, where NEST is preinstalled.

    4) Install Neuro-Workflow, BMTK, and JupyterLab:

         pip install --upgrade pip
         pip install "git+https://github.com/oist/neuro-workflow.git"
         pip install bmtk jupyterlab matplotlib

    5) Verify the installation (NEST should report version 3.7 or newer):

         python -c "import nest, bmtk; from neuroworkflow.core.node import Node; print('NEST', nest.__version__)"

    6) Download the three example notebooks from the repository:

         base=https://raw.githubusercontent.com/oist/neuro-workflow/main/notebooks
         curl -fsSL $base/NW_SingleCell_PointNeuron.ipynb     -o NW_SingleCell_PointNeuron.ipynb
         curl -fsSL $base/NW_BalancedNetwork_PointNeuron.ipynb -o NW_BalancedNetwork_PointNeuron.ipynb
         curl -fsSL $base/NW_Ring_PointNeuron.ipynb           -o NW_Ring_PointNeuron.ipynb

    7) Launch JupyterLab, open the three notebooks, and run them before the hackathon:

         jupyter lab

       Run all three end to end so they execute successfully on your machine. We will explain
       them during the hackathon, and then together we will recreate a version of one of them
       on the server GUI using our Neuro-Workflow AI agents.

Activity 1 — Run the example notebooks locally and learn the Python API

  Three example workflows are provided in the notebooks folder, built with the NW Model
  Builder nodes:

    - NW_SingleCell_PointNeuron.ipynb   — a single point-neuron driven by a current clamp.
    - NW_BalancedNetwork_PointNeuron.ipynb — an excitatory/inhibitory balanced network.
    - NW_Ring_PointNeuron.ipynb         — a ring-topology network.

  Run each notebook locally and follow the Neuro-Workflow Python API as you go. The pattern is
  the same in all three:

    1) Create the nodes.
    2) Configure each node's parameters.
    3) Create a WorkflowBuilder, add the nodes, and connect their ports.
    4) Set the workflow context (e.g. the results path).
    5) Build the workflow and execute it.
    6) Validate the outputs (confirm the run succeeded and no output is empty / None).

  Goal: understand how nodes, parameters, ports, connections, and execution fit together —
  this is the foundation for everything that follows.

Activity 2 — Reproduce one workflow in the GUI on the server

  Choose any one of the three workflows and rebuild it visually in the web application on the
  server. The NW Model Builder nodes are already available on the server, so you do not create
  any node here — you assemble the workflow:

    1) Add the required nodes from the palette.
    2) Connect their ports to form the workflow graph.
    3) Configure the parameters of each node.
    4) Build the workflow, generate the code, and run it.

  Do this with the help of the Neuro-Workflow AI agents (the in-app AI assistant), which can
  add nodes, connect them, and set parameters for you on request.

  Goal: see that the same model you ran locally in Python can be reproduced and executed
  visually on the server.


2. Nodes and Workflow Creation Using AI Coding Agents

This theme is similar to Theme 1, except that here you create the nodes and the workflow from
your own source code, with the help of AI coding agents.

  - You bring your own Python code (a model, a preprocessing or analysis script, a simulation
    — unstructured is fine; that is the starting point).
  - You use an AI coding agent (Claude Code or Codex) guided by our create-node SKILL.md to
    turn that code into Neuro-Workflow nodes and a workflow. The skill encodes the conventions
    and checks we developed from experience building and testing nodes manually, so the agent
    produces clean, uploadable nodes.
  - You run the generated nodes and workflow locally (in a notebook) and validate the outputs.
  - You upload the nodes to the server using the GUI.
  - You create a workflow on the server with the help of the Neuro-Workflow AI agents (the
    in-app AI assistant), the same way as in Theme 1.

The materials for this theme are in the hackathon folder:

  - README.md            — the step-by-step participant agenda.
  - SETUP.md             — environment setup for each agent (scripts + manual fallback).
  - CLAUDE.md / AGENTS.md — the agent instructions (identical; Claude Code reads CLAUDE.md,
                            Codex reads AGENTS.md).
  - create-node SKILL.md — the node-creation skill the agent follows.
  - check_node.py        — a validator that checks each generated node.
  - quick_setup/         — one-command setup scripts (setup_claude.sh, setup_codex.sh).
  - examples/            — a dependency-free example to get a first green run, plus a sample
                            unstructured script to use if you did not bring your own code.

Setup — download the kit, then run the script from your own test folder

  We will provide the hackathon folder. The setup is location-independent: the script reads
  what it needs from the internet and writes the workspace into your current folder. So you
  keep the hackathon folder as shared, read-only material, and run the script from a separate
  test folder of your own.

    1) Download the hackathon folder we provide and store it anywhere on your computer.
       Example: ./hackathon

    2) Create a folder for your test, in any location (inside or outside hackathon), and cd
       into it. Example:

         mkdir ./mytest
         cd ./mytest

    3) From inside your test folder, run the setup script for your agent using the path to
       where you stored the hackathon folder. Example (hackathon is one level up):

         # Claude Code:
         bash ../hackathon/quick_setup/setup_claude.sh
         # Codex:
         bash ../hackathon/quick_setup/setup_codex.sh

  Everything the script creates — the Python virtual environment (venv/), the source_code/ and
  my_nodes/ folders, the create-node skill, and the agent instruction file — is written inside
  your test folder (./mytest), not into the hackathon folder. Put your own code in source_code/;
  the agent writes the generated nodes and workflow into my_nodes/.

  (The script downloads a pinned neuroworkflow + JupyterLab + matplotlib, so you need an
  internet connection the first time you run it. It is safe to re-run.)
