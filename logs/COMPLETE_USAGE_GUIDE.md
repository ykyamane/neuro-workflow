# NeuroWorkflow - Complete Usage Guide

This guide covers all ways to use NeuroWorkflow, from command-line scripts to the web UI.

## Table of Contents

1. [Command-Line Usage](#command-line-usage) ✅ (Already Working!)
2. [Jupyter Notebooks (Interactive)](#jupyter-notebooks-interactive)
3. [Web UI (Visual Workflow Builder)](#web-ui-visual-workflow-builder)
4. [Creating Custom Workflows](#creating-custom-workflows)
5. [Available Node Types](#available-node-types)
6. [Advanced Features](#advanced-features)

---

## Command-Line Usage

### ✅ Already Working!

You've already successfully run a simulation from the command line:

```bash
conda activate neuro
cd /Users/kirill/Documents/digital_brain/neuro-workflow
python examples/sonata_simulation.py
```

### Available Examples

1. **Basic SONATA Simulation** (✅ Working)
   ```bash
   python examples/sonata_simulation.py
   ```

2. **Neuron Optimization**
   ```bash
   python examples/neuron_optimization.py
   ```
   Note: May have some bugs according to README

3. **Epileptic Resting State (TVB)**
   ```bash
   python examples/epilepsy_rs.py
   ```

### Creating Your Own Scripts

Create a new Python file and follow this template:

```python
#!/usr/bin/env python3
import sys
import os

# Add src to path if not installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from neuroworkflow import WorkflowBuilder
from neuroworkflow.nodes.network.BuildSonataNetworkNode import BuildSonataNetworkNode
from neuroworkflow.nodes.simulation.SimulateSonataNetworkNode import SimulateSonataNetworkNode

def main():
    # Get absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    data_path = os.path.join(repo_root, "data", "300_pointneurons")
    
    # Create and configure nodes
    build_network = BuildSonataNetworkNode("NetworkBuilder")
    build_network.configure(
        sonata_path=data_path,
        net_config_file="circuit_config.json",
        sim_config_file="simulation_config.json",
        hdf5_hyperslab_size=1024
    )
    
    simulate_network = SimulateSonataNetworkNode("Simulator")
    simulate_network.configure(
        simulation_time=1000.0,
        record_from_population="internal",
        record_n_neurons=40
    )
    
    # Build workflow
    workflow = (
        WorkflowBuilder("my_workflow")
            .add_node(build_network)
            .add_node(simulate_network)
            .connect("NetworkBuilder", "sonata_net", "Simulator", "sonata_net")
            .connect("NetworkBuilder", "node_collections", "Simulator", "node_collections")
            .build()
    )
    
    # Execute
    print("Executing workflow...")
    success = workflow.execute()
    
    if success:
        print("✓ Workflow completed successfully!")
        return 0
    else:
        print("✗ Workflow failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## Jupyter Notebooks (Interactive)

### Setup

```bash
conda activate neuro
pip install jupyter notebook matplotlib seaborn
```

### Start Jupyter

```bash
cd /Users/kirill/Documents/digital_brain/neuro-workflow
jupyter notebook
```

This will open your browser automatically. Navigate to the `notebooks/` folder.

### Available Notebooks

1. **`01_Basic_Simulation.ipynb`** - Interactive tutorial for basic simulation
   - Step-by-step workflow creation
   - Visualize results
   - Experiment with parameters

2. **`epilepsy_rs.ipynb`** - Epileptic resting state using TVB
   - TVB (The Virtual Brain) integration
   - More complex workflow example

3. **`SNNbuilder_example1.ipynb`** - Spiking Neural Network building
   - Custom SNNbuilder nodes
   - Network construction examples

### Using Notebooks

- **Run cells**: Shift+Enter to execute a cell
- **Run all**: Cell → Run All
- **Add cells**: Click "+" button
- **Save**: Ctrl+S (or Cmd+S on Mac)

Each notebook includes:
- Setup code (adds src to path, imports)
- Step-by-step explanations
- Interactive code cells
- Visualization examples

---

## Web UI (Visual Workflow Builder)

The web UI provides a visual, drag-and-drop interface for building workflows. **Requires Docker.**

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 3000, 5173, 8000 available

### Step 1: Build NEST JupyterLab Image

```bash
cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui/workflow_backend/django-project/neuroworkflow
docker build -t nest-jupyterlab -f Dockerfile.nest .
```

### Step 2: Configure Environment Variables

Create `.env` files from templates:

```bash
# Main GUI .env
cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui
cp env.template .env
# Edit .env with your settings (usually defaults are fine)

# Backend .env
cd workflow_backend
cp env.template .env
# Edit .env if needed

# Frontend .env
cd ../workflow_frontend
cp env.template .env
# Edit .env if needed
```

### Step 3: Start Docker Containers

```bash
cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui
docker-compose build
docker-compose up
```

This starts:
- **Web Frontend** (React/TypeScript) on `http://localhost:5173`
- **Django Backend** on `http://localhost:3000`
- **JupyterHub** on `http://localhost:8000`
- **PostgreSQL Database**

### Step 4: Access the Web UI

1. **Main Application**: Open `http://localhost:5173` in your browser
2. **Django Admin**: `http://localhost:3000/admin` (create superuser first)
3. **JupyterHub**: `http://localhost:8000/` (user: `user1`, password: `password`)

### Step 5: Create Admin User (First Time)

```bash
# In a new terminal
docker-compose exec -it web bash
python django-project/manage.py createsuperuser
# Follow prompts to create admin user
```

### Using the Web UI

The web UI provides:

1. **Visual Workflow Builder**
   - Drag-and-drop nodes
   - Connect nodes visually
   - Configure parameters in UI
   - Save and load workflows

2. **Node Library**
   - Browse available nodes
   - Search by functionality
   - View node documentation

3. **Code Generation**
   - Generate Python code from visual workflow
   - Export workflows as scripts
   - Share workflows

4. **Jupyter Integration**
   - Run workflows in Jupyter notebooks
   - Interactive execution
   - Visualize results

### Stopping the Web UI

```bash
cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui
docker-compose down
```

To stop and remove volumes (clean reset):
```bash
docker-compose down -v
```

---

## Creating Custom Workflows

### Workflow Structure

A workflow consists of:
1. **Nodes** - Processing units
2. **Connections** - Data flow between nodes
3. **Parameters** - Configuration values

### Basic Workflow Pattern

```python
from neuroworkflow import WorkflowBuilder

# 1. Create nodes
node1 = SomeNode("Node1")
node1.configure(param1=value1, param2=value2)

node2 = AnotherNode("Node2")
node2.configure(param1=value1)

# 2. Build workflow
workflow = (
    WorkflowBuilder("workflow_name")
        .add_node(node1)
        .add_node(node2)
        .connect("Node1", "output_port", "Node2", "input_port")
        .build()
)

# 3. Execute
workflow.execute()
```

### Connection Types

- **Data connections**: Pass data between nodes
- **Parameter connections**: Share configuration
- **Multiple outputs**: One node can connect to many

---

## Available Node Types

### Network Nodes

- **`BuildSonataNetworkNode`** - Build network from SONATA format
- **`NESTNeuronSetupNode`** - Setup NEST neurons
- **`SNNbuilder_Population`** - Create neuron populations
- **`SNNbuilder_SingleNeuron`** - Single neuron setup
- **`TVBConnectivitySetUpNode`** - TVB connectivity
- **`TVBEpileptorNode`** - TVB epileptor model

### Simulation Nodes

- **`SimulateSonataNetworkNode`** - Simulate SONATA network
- **`NeuronSimulationNode`** - General neuron simulation
- **`SNNbuilder_Simulation`** - SNNbuilder simulation
- **`TVBSimulatorNode`** - TVB simulation
- **`TVBIntegratorNode`** - TVB integration

### Analysis Nodes

- **`SpikeAnalysisNode`** - Analyze spike data
- **`TVBVisualizationNode`** - Visualize TVB results

### Stimulus Nodes

- **`StimulusGeneratorNode`** - Generate stimuli
- **`SNNbuilder_Stimulation`** - SNNbuilder stimulation
- **`SNNbuilder_Recordable`** - Recording setup
- **`TVBMonitorNode`** - TVB monitoring

### Optimization Nodes

- **`JointOptimizationNode`** - Parameter optimization

### I/O Nodes

- File input/output nodes for data loading and saving

---

## Advanced Features

### Parameter Optimization

Some nodes support parameter optimization:

```python
from neuroworkflow.nodes.optimization import JointOptimizationNode

optimizer = JointOptimizationNode("Optimizer")
optimizer.configure(
    method='bayesian',
    max_iterations=50,
    objective='minimize_error'
)

# Connect to nodes with optimizable parameters
workflow = (
    WorkflowBuilder("optimization_workflow")
        .add_node(data_loader)
        .add_node(processor)  # Has optimizable parameters
        .add_node(evaluator)
        .add_node(optimizer)
        # ... connections
        .build()
)
```

### Custom Nodes

See `CUSTOM_NODE_TUTORIAL.md` for detailed instructions on creating custom nodes.

Quick start:
1. Copy `CustomNodeTemplate.py`
2. Define `NODE_DEFINITION` with parameters, inputs, outputs
3. Implement processing methods
4. Define process steps
5. Use in workflows

### Workflow Export

Export workflows as Python scripts:

```python
# In web UI: Use code generation feature
# Or programmatically:
workflow_code = workflow.export_to_python()
with open("my_workflow.py", "w") as f:
    f.write(workflow_code)
```

### Batch Processing

Run multiple workflows:

```python
configs = [
    {"simulation_time": 1000, "record_n_neurons": 40},
    {"simulation_time": 2000, "record_n_neurons": 80},
    {"simulation_time": 500, "record_n_neurons": 20},
]

for i, config in enumerate(configs):
    workflow = create_workflow(config)
    success = workflow.execute()
    print(f"Workflow {i+1}: {'Success' if success else 'Failed'}")
```

---

## Quick Reference

### Command-Line
```bash
# Activate environment
conda activate neuro

# Run example
python examples/sonata_simulation.py

# Start Jupyter
jupyter notebook
```

### Web UI
```bash
# Start
cd gui
docker-compose up

# Stop
docker-compose down

# Access
# Frontend: http://localhost:5173
# Admin: http://localhost:3000/admin
# JupyterHub: http://localhost:8000
```

### Common Workflow Pattern
```python
# 1. Create nodes
# 2. Configure nodes
# 3. Build workflow with connections
# 4. Execute
```

---

## Troubleshooting

### Command-Line Issues

**Import errors**: Make sure you're in the `neuro` conda environment
```bash
conda activate neuro
```

**Path errors**: Use absolute paths in your scripts (see example fix)

**Missing dependencies**: Install with conda
```bash
conda install -n neuro <package-name>
```

### Web UI Issues

**Docker won't start**: Check Docker is running
```bash
docker ps
```

**Port conflicts**: Check if ports are in use
```bash
lsof -i :3000 -i :5173 -i :8000
```

**Database issues**: Reset database
```bash
docker-compose down -v
docker-compose up
```

**Build errors**: Rebuild containers
```bash
docker-compose build --no-cache
docker-compose up
```

---

## Next Steps

1. ✅ **Command-line usage** - You've got this working!
2. **Try Jupyter notebooks** - Interactive exploration
3. **Set up Web UI** - Visual workflow building
4. **Create custom workflows** - Build your own simulations
5. **Explore node types** - See what's available
6. **Create custom nodes** - Extend the system

---

## Getting Help

- **Documentation**: Check `README.md`, `CUSTOM_NODE_TUTORIAL.md`, `NODE_SCHEMA.md`
- **Examples**: Look at `examples/` and `notebooks/`
- **Repository**: https://github.com/oist/neuro-workflow

Happy workflow building! 🧠⚙️

