# Node Connections and Data Flow Guide

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Port System](#port-system)
3. [How Connections Work](#how-connections-work)
4. [Data Flow Mechanism](#data-flow-mechanism)
5. [Execution Order](#execution-order)
6. [Brain Modeling Example](#brain-modeling-example)
7. [Using Connections in the GUI](#using-connections-in-the-gui)
8. [Common Patterns](#common-patterns)

---

## Core Concepts

### What is a Node?

A **node** is a self-contained processing unit that:
- Takes **inputs** through **input ports**
- Performs some computation or operation
- Produces **outputs** through **output ports**
- Has **parameters** that control its behavior

Think of a node like a function in programming, but with a visual interface.

### What is a Port?

A **port** is a connection point on a node:
- **Input Port**: Where data **enters** the node (like function parameters)
- **Output Port**: Where data **exits** the node (like function return values)

### What is a Connection?

A **connection** links an output port of one node to an input port of another node, allowing data to flow from the source node to the target node.

---

## Port System

### Port Types

Ports have two important properties:

1. **Data Type**: What kind of data the port expects/produces
   - `int`, `float`, `str`, `bool`
   - `list`, `dict`
   - Custom objects (e.g., NEST network objects, population data)

2. **Port Type** (for HPC/SnakeMake):
   - **Memory Port**: Data stays in memory (for in-process workflows)
   - **I/O Port**: Data is file-based (for HPC workflows)
     - `FILE_PATH`, `HDF5_FILE`, `CSV_FILE`, `JSON_FILE`, etc.

### Input Ports

```python
# Input port characteristics:
- Receives data from other nodes OR manual input
- Can be optional or required
- Has a data type that must match the source
- Can have a default value if not connected
```

**Example**: A neuron node might have:
- `population_data` (input): Receives population information from a network builder
- `stimulation_params` (input, optional): Receives stimulation parameters

### Output Ports

```python
# Output port characteristics:
- Produces data that can be used by other nodes
- Can connect to multiple input ports (one-to-many)
- Has a data type that must match target inputs
```

**Example**: A network builder node might have:
- `sonata_net` (output): Produces a SONATA network object
- `node_collections` (output): Produces neuron population metadata

---

## How Connections Work

### Connection Structure

A connection is defined as:
```
SourceNode.output_port → TargetNode.input_port
```

**Visual representation**:
```
┌─────────────────┐         ┌─────────────────┐
│  Source Node    │         │  Target Node    │
│                 │         │                 │
│  [output_port]──┼─────────┼→[input_port]    │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
```

### Connection Rules

1. **Type Compatibility**: The output port type must be compatible with the input port type
   - Same type: ✅ Compatible
   - Subtype: ✅ Compatible (e.g., `int` → `float`)
   - Different types: ❌ Incompatible (connection rejected)

2. **One-to-Many**: One output port can connect to multiple input ports
   ```
   NodeA.output → NodeB.input1
   NodeA.output → NodeC.input1
   NodeA.output → NodeD.input1
   ```

3. **Many-to-One**: Multiple output ports can connect to the same input port (if the input accepts it)
   - This is less common and depends on the input port's design

4. **No Cycles**: The workflow must be a Directed Acyclic Graph (DAG)
   - ❌ NodeA → NodeB → NodeA (cycle - not allowed)
   - ✅ NodeA → NodeB → NodeC (linear - allowed)

### Making Connections

**In Code**:
```python
# Connect NodeA's output to NodeB's input
node_a.connect_to('output_port_name', node_b, 'input_port_name')
```

**In GUI**:
1. Click and drag from an output port (right side of node)
2. Release on an input port (left side of target node)
3. The system checks type compatibility automatically

---

## Data Flow Mechanism

### Step-by-Step Data Flow

Let's trace how data flows through a connection:

#### 1. Source Node Executes

```python
# Source node (e.g., BuildSonataNetworkNode) executes
def process(self):
    # ... node does its work ...
    
    # Node produces output
    sonata_network = self._build_network()
    
    # Set output port value
    self._output_ports['sonata_net'].set_value(sonata_network)
    
    # Propagate to connected nodes
    self._output_ports['sonata_net'].propagate()
```

#### 2. Value Propagation

```python
# OutputPort.propagate() method
def propagate(self):
    """Propagate the value to connected input ports."""
    for input_port in self.connected_to:
        input_port.set_value(self.value)
```

#### 3. Target Node Receives Data

```python
# Target node (e.g., SimulateSonataNetworkNode) needs the data
def process(self):
    # Get value from input port
    # If connected, gets value from source
    # If not connected, gets local/default value
    sonata_net = self._input_ports['sonata_net'].get_value()
    
    # Use the data
    self._simulate(sonata_net)
```

### Input Port Value Resolution

The `InputPort.get_value()` method is smart:

```python
def get_value(self) -> Any:
    """Get the value of this port."""
    if self.connected_to is not None:
        # Connected: get value from source output port
        return self.connected_to.value
    else:
        # Not connected: return local/default value
        return self.value
```

This means:
- **If connected**: Data comes from the source node automatically
- **If not connected**: You can set a default value manually

---

## Execution Order

### Dependency Resolution

The workflow system uses **topological sorting** to determine execution order:

1. **Build Dependency Graph**: Analyze all connections
   ```
   NodeA → NodeB → NodeC
   NodeA → NodeD
   ```
   Creates dependencies:
   - NodeB depends on NodeA
   - NodeC depends on NodeB
   - NodeD depends on NodeA

2. **Compute Execution Order**: Nodes with no dependencies execute first
   ```
   Execution Order:
   1. NodeA (no dependencies)
   2. NodeB, NodeD (depend only on NodeA - can run in parallel)
   3. NodeC (depends on NodeB)
   ```

3. **Execute Sequentially**: Process nodes in computed order
   - Each node waits for its dependencies to complete
   - Data is automatically available when node executes

### Example Execution Flow

```
Workflow: Network Build → Neuron Setup → Connection → Simulation

Step 1: BuildSonataNetworkNode executes
  ├─ Reads: sonata_path (parameter)
  ├─ Produces: sonata_net (output)
  └─ Sets: sonata_net output port value

Step 2: SNNbuilder_SingleNeuron executes
  ├─ Reads: population_data (from BuildSonataNetworkNode)
  ├─ Produces: neuron_population (output)
  └─ Sets: neuron_population output port value

Step 3: SNNbuilder_Connection executes
  ├─ Reads: source_population_metadata (from SNNbuilder_SingleNeuron)
  ├─ Reads: target_population_metadata (from BuildSonataNetworkNode)
  ├─ Produces: connections (output)
  └─ Sets: connections output port value

Step 4: SNNbuilder_Simulation executes
  ├─ Reads: network_data (from BuildSonataNetworkNode)
  ├─ Reads: connections (from SNNbuilder_Connection)
  ├─ Produces: simulation_results (output)
  └─ Sets: simulation_results output port value
```

---

## Brain Modeling Example

### Complete Workflow: Mouse Cortical Network Simulation

Let's build a realistic brain modeling workflow:

#### Step 1: Build Network Structure

**Node**: `BuildSonataNetworkNode`
- **Inputs**: None (starts the workflow)
- **Parameters**:
  - `sonata_path`: Path to SONATA network files
  - `net_config_file`: Network configuration
  - `sim_config_file`: Simulation configuration
- **Outputs**:
  - `sonata_net`: SONATA network object
  - `node_collections`: Population metadata

**What it does**: Loads a pre-built network structure (e.g., 300 point neurons)

#### Step 2: Configure Neurons

**Node**: `SNNbuilder_SingleNeuron`
- **Inputs**:
  - `population_data`: From BuildSonataNetworkNode.node_collections
- **Parameters**:
  - `name`: "Layer5_Pyramidal"
  - `cell_class`: "excitatory"
  - `firing_rate`: 5.0 Hz (could come from metadata service!)
  - `membrane_capacitance`: 100.0 pF
- **Outputs**:
  - `neuron_population`: Configured neuron population
  - `population_metadata`: Metadata about the population

**What it does**: Configures neuron properties for a specific population

#### Step 3: Create Connections

**Node**: `SNNbuilder_Connection`
- **Inputs**:
  - `source_population_metadata`: From SNNbuilder_SingleNeuron
  - `target_population_metadata`: From BuildSonataNetworkNode (or another neuron node)
- **Parameters**:
  - `connection_rule`: "all_to_all"
  - `synapse_model`: "static_synapse"
  - `weight`: 1.0
- **Outputs**:
  - `connections`: Connection data
  - `connection_metadata`: Connection information

**What it does**: Creates synaptic connections between neuron populations

#### Step 4: Add Stimulation

**Node**: `SNNbuilder_Stimulation`
- **Inputs**:
  - `population_data`: From SNNbuilder_SingleNeuron
- **Parameters**:
  - `stimulation_type`: "poisson_generator"
  - `rate`: 10.0 Hz
- **Outputs**:
  - `stimulation_devices`: Stimulation device objects

**What it does**: Adds external stimulation to neurons

#### Step 5: Set Up Recording

**Node**: `SNNbuilder_Recordable`
- **Inputs**:
  - `population_data`: From SNNbuilder_SingleNeuron
- **Parameters**:
  - `recording_type`: "spike_recorder"
  - `record_from_population`: 100 (number of neurons)
- **Outputs**:
  - `recording_devices`: Recording device objects

**What it does**: Sets up devices to record neural activity

#### Step 6: Run Simulation

**Node**: `SNNbuilder_Simulation` or `SimulateSonataNetworkNode`
- **Inputs**:
  - `sonata_net`: From BuildSonataNetworkNode
  - `node_collections`: From BuildSonataNetworkNode
  - `connections`: From SNNbuilder_Connection (if using SNNbuilder)
  - `stimulation_devices`: From SNNbuilder_Stimulation (if using SNNbuilder)
  - `recording_devices`: From SNNbuilder_Recordable (if using SNNbuilder)
- **Parameters**:
  - `simulation_time`: 1000.0 ms
  - `dt`: 0.1 ms
- **Outputs**:
  - `simulation_results`: Spike data, membrane potentials, etc.
  - `python_script`: Generated Python code

**What it does**: Executes the simulation and produces results

### Visual Workflow Diagram

```
┌─────────────────────────┐
│ BuildSonataNetworkNode  │
│                         │
│ Outputs:                │
│ • sonata_net            │
│ • node_collections      │
└──────┬──────────┬───────┘
       │          │
       │          └─────────────────┐
       │                            │
       ▼                            ▼
┌──────────────────┐      ┌──────────────────┐
│SNNbuilder_       │      │SNNbuilder_       │
│SingleNeuron      │      │SingleNeuron      │
│                  │      │                  │
│ Input:           │      │ Input:           │
│ • population_data│      │ • population_data│
│                  │      │                  │
│ Output:          │      │ Output:          │
│ • neuron_pop     │      │ • neuron_pop     │
│ • metadata       │      │ • metadata       │
└──────┬───────────┘      └──────┬───────────┘
       │                         │
       │                         │
       └──────────┬──────────────┘
                  │
                  ▼
         ┌──────────────────┐
         │SNNbuilder_        │
         │Connection         │
         │                   │
         │ Inputs:           │
         │ • source_meta    │
         │ • target_meta     │
         │                   │
         │ Output:           │
         │ • connections     │
         └─────────┬─────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌──────────────────┐  ┌──────────────────┐
│SNNbuilder_       │  │SNNbuilder_       │
│Stimulation       │  │Recordable        │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
         ┌──────────────────┐
         │SNNbuilder_        │
         │Simulation         │
         │                   │
         │ Inputs:           │
         │ • sonata_net      │
         │ • connections     │
         │ • stimulation     │
         │ • recording       │
         │                   │
         │ Output:           │
         │ • results         │
         │ • python_script   │
         └───────────────────┘
```

---

## Using Connections in the GUI

### Step-by-Step: Creating a Connected Workflow

#### 1. Add Nodes to Canvas

1. Open the workflow editor (`http://localhost:5173`)
2. Click "Add Node" or drag from the node palette
3. Add nodes in this order:
   - `BuildSonataNetworkNode`
   - `SNNbuilder_SingleNeuron`
   - `SNNbuilder_Connection`
   - `SNNbuilder_Simulation`

#### 2. Configure Node Parameters

1. Click on `BuildSonataNetworkNode`
2. In the right panel, set parameters:
   - `sonata_path`: `/path/to/network/data`
   - `net_config_file`: `circuit_config.json`
   - `sim_config_file`: `simulation_config.json`
3. Click "Save" or the node auto-saves

#### 3. Create Connections

**Method 1: Drag and Drop**
1. Hover over `BuildSonataNetworkNode`
2. You'll see output ports on the right side (small circles)
3. Click and drag from `node_collections` output port
4. Drag to `SNNbuilder_SingleNeuron` on the left side
5. Release over the `population_data` input port
6. A connection line appears if types are compatible

**Method 2: Connection Menu**
1. Click on `BuildSonataNetworkNode`
2. Right-click on an output port
3. Select "Connect to..."
4. Choose target node and input port from menu

#### 4. Verify Connections

- **Visual Check**: Connection lines should appear between nodes
- **Type Check**: Incompatible connections are rejected (red line or error message)
- **Port Info**: Hover over ports to see their types and descriptions

#### 5. Execute Workflow

1. Click "Execute" or "Run Workflow" button
2. System automatically:
   - Computes execution order
   - Executes nodes in correct sequence
   - Passes data through connections
3. View results in output ports or generated scripts

---

## Common Patterns

### Pattern 1: Linear Pipeline

```
NodeA → NodeB → NodeC → NodeD
```

**Use case**: Sequential processing steps
**Example**: Network → Neuron Config → Simulation → Analysis

### Pattern 2: Fan-Out (One-to-Many)

```
        ┌─→ NodeB
NodeA ──┼─→ NodeC
        └─→ NodeD
```

**Use case**: Same data used by multiple nodes
**Example**: Network structure used by multiple neuron configurations

### Pattern 3: Fan-In (Many-to-One)

```
NodeA ──┐
NodeB ──┼─→ NodeD
NodeC ──┘
```

**Use case**: Combining multiple data sources
**Example**: Multiple neuron populations → Single connection node

### Pattern 4: Parallel Processing

```
NodeA ──→ NodeB ──→ NodeE
     └─→ NodeC ──┘
     └─→ NodeD ──┘
```

**Use case**: Independent processing branches
**Example**: Different neuron types configured in parallel

---

## Key Principles for Brain Modeling

### 1. Start with Structure

Always begin with a network/structure builder node:
- `BuildSonataNetworkNode`: Loads existing network
- `TVBConnectivitySetUpNode`: Sets up connectivity matrix

### 2. Configure Components

Then configure individual components:
- Neurons: `SNNbuilder_SingleNeuron`
- Connections: `SNNbuilder_Connection`
- Stimulation: `SNNbuilder_Stimulation`

### 3. Connect in Logical Order

Connect based on data dependencies:
- Network structure → Neuron configuration
- Neuron metadata → Connection setup
- All components → Simulation

### 4. Use Metadata Flow

Many nodes output metadata that other nodes need:
- `node_collections` → Used by neuron nodes
- `population_metadata` → Used by connection nodes
- This metadata flows automatically through connections

### 5. End with Execution

Final node should be a simulation/execution node:
- `SNNbuilder_Simulation`
- `SimulateSonataNetworkNode`
- `TVBSimulatorNode`

---

## Troubleshooting Connections

### Problem: Connection Rejected

**Cause**: Type mismatch
**Solution**: Check port types - they must be compatible

### Problem: Node Executes Before Data Available

**Cause**: Execution order incorrect
**Solution**: System should handle this automatically, but check for cycles

### Problem: Missing Data in Node

**Cause**: Input port not connected and no default value
**Solution**: Either connect the port or set a default value in node parameters

### Problem: Multiple Connections to Same Input

**Cause**: Input port doesn't support multiple sources
**Solution**: Use a merge/combine node or connect to different inputs

---

## Advanced: Understanding Port Types

### Memory Ports (In-Process)

- Data stays in Python memory
- Fast for local execution
- Used for: NEST objects, Python dictionaries, NumPy arrays

### I/O Ports (HPC-Ready)

- Data is file-based
- Used for SnakeMake/HPC workflows
- Types: `HDF5_FILE`, `CSV_FILE`, `JSON_FILE`
- Files are automatically managed by the workflow system

**Example**:
```python
# Node outputs HDF5 file path
output_port.type = PortType.HDF5_FILE
output_port.value = "/path/to/results.h5"

# Next node reads from file
input_port.type = PortType.HDF5_FILE
input_port.value = "/path/to/results.h5"  # Automatically set by connection
```

---

## Summary

1. **Nodes** process data through **ports**
2. **Connections** link output ports to input ports
3. **Data flows** automatically when nodes execute
4. **Execution order** is computed from dependencies
5. **Type checking** ensures data compatibility
6. **Brain modeling** follows: Structure → Components → Connections → Simulation

The system handles all the complexity - you just connect the nodes logically!

---

*For more details, see:*
- `docs/ARCHITECTURE.md` - System architecture
- `NODE_SCHEMA.md` - Node schema reference
- `CUSTOM_NODE_TUTORIAL.md` - Creating custom nodes

