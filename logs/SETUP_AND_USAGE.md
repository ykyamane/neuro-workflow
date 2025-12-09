# NeuroWorkflow - Setup and Usage Guide

This guide provides detailed instructions for setting up and using the NeuroWorkflow library.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Basic Usage (Python Scripts)](#basic-usage-python-scripts)
4. [Using Jupyter Notebooks](#using-jupyter-notebooks)
5. [GUI/Web Interface (Optional)](#guiweb-interface-optional)
6. [Creating Custom Nodes](#creating-custom-nodes)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8 or higher** installed
- **pip** (Python package manager)
- **Git** (already installed since you cloned the repo)
- **NEST Simulator** (optional, for neural simulations) - install with: `pip install nest-simulator` or follow [NEST installation guide](https://nest-simulator.readthedocs.io/en/stable/installation/index.html)
- **Docker** (optional, only needed for GUI/web interface)

---

## Installation

### Option 1: Install as a Package (Recommended)

Install the library in development mode so you can edit the source code:

```bash
cd /Users/kirill/Documents/digital_brain/neuro-workflow
pip install -e .
```

This installs the package in "editable" mode, meaning changes to the source code are immediately available.

### Option 2: Add to Python Path (Quick Start)

If you don't want to install the package, you can add the `src` directory to your Python path in your scripts:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

### Install Optional Dependencies

For neural simulations with NEST:
```bash
pip install nest-simulator
```

For visualization:
```bash
pip install matplotlib seaborn
```

For development tools:
```bash
pip install pytest black isort mypy
```

Or install all optional dependencies:
```bash
pip install -e ".[nest,visualization,dev]"
```

---

## Basic Usage (Python Scripts)

### Example 1: Simple Simulation

The repository includes a basic simulation example. Run it with:

```bash
cd /Users/kirill/Documents/digital_brain/neuro-workflow
python examples/sonata_simulation.py
```

**What this does:**
- Creates a neural network from SONATA format data
- Simulates the network using NEST
- Records spikes from 40 neurons
- Runs for 1000ms

### Example 2: Create Your Own Workflow

Here's a template for creating your own workflow:

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
    # Step 1: Create nodes
    build_network = BuildSonataNetworkNode("NetworkBuilder")
    build_network.configure(
        sonata_path="data/300_pointneurons",
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
    
    # Step 2: Build workflow
    workflow = (
        WorkflowBuilder("my_workflow")
            .add_node(build_network)
            .add_node(simulate_network)
            .connect("NetworkBuilder", "sonata_net", "Simulator", "sonata_net")
            .connect("NetworkBuilder", "node_collections", "Simulator", "node_collections")
            .build()
    )
    
    # Step 3: Execute
    print("Executing workflow...")
    success = workflow.execute()
    
    if success:
        print("Workflow completed successfully!")
    else:
        print("Workflow failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Understanding the Workflow Structure

1. **Create Nodes**: Instantiate node classes with unique names
2. **Configure Nodes**: Set parameters using the `configure()` method
3. **Build Workflow**: Use `WorkflowBuilder` to:
   - Add nodes with `.add_node()`
   - Connect nodes with `.connect(source_node, output_port, target_node, input_port)`
   - Build with `.build()`
4. **Execute**: Call `workflow.execute()` to run the workflow

---

## Using Jupyter Notebooks

The repository includes several interactive Jupyter notebooks:

### Available Notebooks

1. **`notebooks/01_Basic_Simulation.ipynb`** - Basic simulation tutorial
2. **`notebooks/epilepsy_rs.ipynb`** - Epileptic resting state example using TVB
3. **`notebooks/SNNbuilder_example1.ipynb`** - Spiking Neural Network building example

### Running Notebooks

1. **Install Jupyter** (if not already installed):
   ```bash
   pip install jupyter notebook
   ```

2. **Start Jupyter Notebook**:
   ```bash
   cd /Users/kirill/Documents/digital_brain/neuro-workflow
   jupyter notebook
   ```

3. **Open a notebook**: Navigate to the `notebooks/` folder and open any `.ipynb` file

4. **Run cells**: Execute cells sequentially using Shift+Enter

### Notebook Setup

Each notebook includes setup code at the beginning that:
- Adds the `src` directory to Python path
- Imports necessary NeuroWorkflow components
- Initializes NEST (if needed)

---

## GUI/Web Interface (Optional)

The repository includes a web-based GUI for visual workflow building. This requires Docker.

### Prerequisites for GUI

- Docker and Docker Compose installed
- At least 4GB of available RAM
- Ports 3000, 5173, 8000 available

### Setup Steps

1. **Navigate to GUI directory**:
   ```bash
   cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui
   ```

2. **Configure environment variables**:
   
   Create `.env` files from templates:
   ```bash
   # Main GUI .env
   cp env.template .env
   # Edit .env with your settings
   
   # Backend .env
   cd workflow_backend
   cp env.template .env
   # Edit .env with your settings
   cd ..
   
   # Frontend .env
   cd workflow_frontend
   cp env.template .env
   # Edit .env with your settings
   cd ..
   ```

3. **Build NEST JupyterLab image** (for backend):
   ```bash
   cd workflow_backend/django-project/neuroworkflow
   docker build -t nest-jupyterlab -f Dockerfile.nest .
   ```

4. **Build and start containers**:
   ```bash
   cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui
   docker-compose build
   docker-compose up
   ```

5. **Access the web interface**:
   - Open your browser to: `http://localhost:5173`
   - Django admin: `http://localhost:3000/admin`
   - JupyterHub: `http://localhost:8000/` (user: `user1`, password: `password`)

### Creating Admin User (First Time)

```bash
docker-compose exec -it web bash
python django-project/manage.py createsuperuser
# Follow prompts to create admin user
```

### Stopping the GUI

```bash
cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui
docker-compose down
```

---

## Creating Custom Nodes

The repository includes comprehensive documentation for creating custom nodes:

1. **Read the tutorial**: `CUSTOM_NODE_TUTORIAL.md`
2. **Use the template**: `CustomNodeTemplate.py`
3. **Check the schema**: `NODE_SCHEMA.md`

### Quick Start for Custom Nodes

1. **Copy the template**:
   ```bash
   cp CustomNodeTemplate.py src/neuroworkflow/nodes/my_custom_node.py
   ```

2. **Edit the template**:
   - Change the class name
   - Define `NODE_DEFINITION` with your parameters, inputs, and outputs
   - Implement your processing methods
   - Define process steps

3. **Use your node**:
   ```python
   from neuroworkflow.nodes.my_custom_node import MyCustomNode
   
   my_node = MyCustomNode("MyNode")
   my_node.configure(parameter1=value1, parameter2=value2)
   # Add to workflow...
   ```

See `CUSTOM_NODE_TUTORIAL.md` for detailed instructions.

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'neuroworkflow'`

**Solutions**:
1. Install the package: `pip install -e .`
2. Or add to path in your script:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
   ```

### NEST Simulator Issues

**Problem**: NEST not found or import errors

**Solutions**:
1. Install NEST: `pip install nest-simulator`
2. Or use conda: `conda install -c conda-forge nest-simulator`
3. Check NEST installation: `python -c "import nest; nest.version()"`

### Path Issues

**Problem**: File not found errors when running examples

**Solutions**:
1. Run scripts from the repository root directory
2. Use absolute paths in your code
3. Check that data files exist in `data/300_pointneurons/`

### Docker/GUI Issues

**Problem**: Docker containers won't start

**Solutions**:
1. Check Docker is running: `docker ps`
2. Check ports are available: `lsof -i :3000 -i :5173 -i :8000`
3. Rebuild containers: `docker-compose down -v && docker-compose build`
4. Check logs: `docker-compose logs`

### Workflow Execution Errors

**Problem**: Workflow fails during execution

**Solutions**:
1. Check node connections are correct
2. Verify all required inputs are connected
3. Check parameter values are valid
4. Enable debug logging in nodes
5. Check NEST is properly initialized

---

## Next Steps

1. **Explore examples**: Run the example scripts in `examples/`
2. **Try notebooks**: Open and run the Jupyter notebooks
3. **Read documentation**: Check `CUSTOM_NODE_TUTORIAL.md` and `NODE_SCHEMA.md`
4. **Build custom workflows**: Create your own workflows for your research
5. **Create custom nodes**: Extend the library with your own processing nodes

---

## Getting Help

- Check the repository: https://github.com/oist/neuro-workflow
- Review example code in `examples/` and `notebooks/`
- Read the documentation files:
  - `README.md` - Overview
  - `CUSTOM_NODE_TUTORIAL.md` - Creating custom nodes
  - `NODE_SCHEMA.md` - Node schema reference

---

## Summary of Quick Commands

```bash
# Install the package
pip install -e .

# Run basic example
python examples/sonata_simulation.py

# Start Jupyter notebooks
jupyter notebook

# Start GUI (requires Docker)
cd gui
docker-compose up

# Install with all dependencies
pip install -e ".[nest,visualization,dev]"
```

Happy workflow building! 🧠⚙️

