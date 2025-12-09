# NeuroWorkflow Node Schema Documentation

This document provides a comprehensive guide to the node schema used in the NeuroWorkflow package. The schema defines how nodes are structured, how they communicate with each other, and how they process data in neural simulation workflows.

## Table of Contents

1. [Overview](#overview)
2. [Node Definition Schema](#node-definition-schema)
3. [Port System](#port-system)
4. [Parameters](#parameters)
5. [Parameter Optimization](#parameter-optimization)
6. [Methods](#methods)
7. [Process Steps](#process-steps)
8. [Creating Custom Nodes](#creating-custom-nodes)
9. [Example Node Implementation](#example-node-implementation)

## Overview

NeuroWorkflow uses a node-based architecture where each node represents a specific processing step in a neural simulation workflow. Nodes are connected through ports, which define the inputs and outputs of each node. The schema provides a standardized way to define nodes, ensuring type safety and proper data flow between components.

Key components of the node schema:

- **Node Definition**: Describes the node's type, inputs, outputs, parameters, and methods
- **Ports**: Define the data entry and exit points for a node
- **Parameters**: Configurable values that control the node's behavior
- **Methods**: Functions that implement the node's processing logic
- **Process Steps**: Ordered sequence of method executions within a node

## Node Definition Schema

The `NodeDefinitionSchema` is the core of the node system. It defines all aspects of a node's structure and behavior.

```python
@dataclass
class NodeDefinitionSchema:
    type: str                  # Unique identifier for the node type
    description: str           # Human-readable description of the node
    parameters: Dict[str, Union[ParameterDefinition, Dict[str, Any], Any]] = field(default_factory=dict)
    inputs: Dict[str, Union[PortDefinition, Dict[str, Any], str]] = field(default_factory=dict)
    outputs: Dict[str, Union[PortDefinition, Dict[str, Any], str]] = field(default_factory=dict)
    methods: Dict[str, Union[MethodDefinition, Dict[str, Any], str]] = field(default_factory=dict)
```

Each node class must define a `NODE_DEFINITION` class variable using this schema. This definition is used to:

1. Auto-generate input and output ports
2. Initialize default parameter values
3. Document the node's capabilities
4. Validate connections between nodes

## Port System

Ports are the connection points between nodes. They define the data types that can flow through them and enforce type safety in the workflow.

### Port Types

The `PortType` enum defines the basic data types supported by the port system:

```python
class PortType(Enum):
    ANY = auto()      # Any type (no type checking)
    INT = auto()      # Integer values
    FLOAT = auto()    # Floating-point values
    STR = auto()      # String values
    BOOL = auto()     # Boolean values
    LIST = auto()     # List of values
    DICT = auto()     # Dictionary of values
    OBJECT = auto()   # Custom object
```

### Port Definition

Ports are defined using the `PortDefinition` class:

```python
@dataclass
class PortDefinition:
    type: Union[PortType, Type] = PortType.ANY  # Data type (PortType enum or Python type)
    description: str = ""                       # Human-readable description
    optional: bool = False                      # Whether this port is required
```

### Input and Output Ports

The system distinguishes between input and output ports:

- **Input Ports**: Receive data from other nodes or external sources
- **Output Ports**: Send data to other nodes

Ports are automatically created from the `NODE_DEFINITION` schema when a node is instantiated.

### Port Compatibility

Ports enforce type compatibility when connecting nodes:

1. `ANY` type is compatible with any other type
2. A port can receive data of its own type or any subclass
3. Special handling for numeric types (int can be converted to float)

## Parameters

Parameters are configurable values that control a node's behavior. They are defined using the `ParameterDefinition` class:

```python
@dataclass
class ParameterDefinition:
    default_value: Any = None                # Default value for the parameter
    description: str = ""                    # Human-readable description
    constraints: Dict[str, Any] = field(default_factory=dict)  # Validation constraints
    optimizable: bool = False                # Whether this parameter can be optimized
    optimization_range: Optional[List] = None  # Range for optimization [min, max]
```

### Parameter Constraints and Optimization

Parameters can have constraints that validate their values:

- **min/max**: Minimum and maximum values for numeric parameters
- **allowed_values**: List of allowed values
- **min_length/max_length**: Constraints for list or string length

Additionally, parameters can be marked as optimizable, which indicates that their values should be explored within a specified range during optimization processes:

- **optimizable**: Boolean flag indicating whether this parameter should be optimized
- **optimization_range**: A list specifying the range [min, max] for optimization

This optimization metadata is particularly useful for parameter sweeps, hyperparameter tuning, and automated optimization of neural simulation parameters.

Example of an optimizable parameter:

```python
'learning_rate': ParameterDefinition(
    default_value=0.01,
    description='Learning rate for the neural network',
    constraints={'min': 0.0001, 'max': 0.1},
    optimizable=True,
    optimization_range=[0.0001, 0.1]
)
```

Parameters are accessed within node methods using the `self._parameters` dictionary.

## Parameter Optimization

Neural simulations often require tuning of parameters to achieve optimal results. The NeuroWorkflow schema supports parameter optimization through metadata in the parameter definitions.

### Optimization Metadata

When defining parameters, you can specify:

1. **optimizable**: A boolean flag indicating whether this parameter should be considered for optimization
2. **optimization_range**: The range [min, max] within which the parameter value should be explored

```python
'learning_rate': ParameterDefinition(
    default_value=0.01,
    description='Learning rate for the neural network',
    constraints={'min': 0.0001, 'max': 0.1},
    optimizable=True,
    optimization_range=[0.0001, 0.1]
)
```

### Optimization Strategies

The optimization metadata enables various optimization strategies:

1. **Grid Search**: Systematically exploring parameter combinations within the specified ranges
2. **Random Search**: Randomly sampling parameter values from the specified ranges
3. **Bayesian Optimization**: Using probabilistic models to guide the search for optimal parameters
4. **Evolutionary Algorithms**: Using genetic algorithms or other evolutionary approaches to optimize parameters

### Implementing Optimization

To implement parameter optimization in a workflow:

1. Identify parameters that should be optimized and mark them with `optimizable=True`
2. Define appropriate optimization ranges based on domain knowledge
3. Create an optimization loop that:
   - Sets parameter values within the node
   - Executes the workflow
   - Evaluates the results using an objective function
   - Updates parameter values based on the optimization strategy

#### Objective Functions

A key component of parameter optimization is the objective function, which evaluates how well a particular parameter set performs. In the NeuroWorkflow system, objective functions:

1. Take simulation results and target values as input
2. Return an error or fitness value
3. Can be customized for specific optimization goals

#### Connecting Nodes in a Workflow

Nodes should be properly connected in a workflow using the `connect` method of the `WorkflowBuilder`. This ensures that data flows automatically between nodes:

```python
# Create nodes
setup_node = NeuronSetupNode("neuron_setup")
stimulus_node = StimulusGeneratorNode("stimulus_generator")
simulation_node = NeuronSimulationNode("neuron_simulation")
optimization_node = NeuronOptimizationNode("neuron_optimization")

# Create a workflow with connected nodes
workflow = (
    WorkflowBuilder("neuron_optimization_workflow")
    .add_node(setup_node)
    .add_node(stimulus_node)
    .add_node(simulation_node)
    .add_node(optimization_node)
    # Connect setup node to simulation node
    .connect("neuron_setup", "neuron_model", "neuron_simulation", "neuron_model")
    # Connect stimulus node to simulation node
    .connect("stimulus_generator", "input_current", "neuron_simulation", "input_current")
    # Connect simulation node to optimization node
    .connect("neuron_simulation", "simulation_results", "neuron_optimization", "simulation_results")
    # Connect optimization node back to setup node to complete the loop
    .connect("neuron_optimization", "parameters", "neuron_setup", "parameters")
    .build()
)
```

The `connect` method takes four arguments:

1. Source node name
2. Source port name
3. Target node name
4. Target port name

## Methods

Methods define the processing logic of a node. They are documented using the `MethodDefinition` class:

```python
@dataclass
class MethodDefinition:
    description: str = ""                     # Human-readable description
    inputs: List[str] = field(default_factory=list)  # Input names used by this method
    outputs: List[str] = field(default_factory=list) # Output names produced by this method
```

Methods are implemented as regular Python methods in the node class. The `MethodDefinition` provides documentation and helps with automatic process step creation.

## Process Steps

Process steps define the execution sequence within a node. Each step corresponds to a method call with defined inputs and outputs.

```python
class ProcessStep:
    def __init__(self, name: str, method: Callable, description: str = "",
                inputs: List[str] = None, outputs: List[str] = None, method_key: str = None):
        # ...
```

Process steps are typically defined in the `_define_process_steps` method of a node class. They can be created automatically from the `NODE_DEFINITION.methods` dictionary.

## Creating Custom Nodes

To create a custom node:

1. Subclass the `Node` base class
2. Define a `NODE_DEFINITION` class variable using `NodeDefinitionSchema`
3. Implement the required methods
4. Override `_define_process_steps` to set up the execution sequence

Basic structure of a custom node:

```python
class MyCustomNode(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type='my_custom_node',
        description='Description of my custom node',
        parameters={
            'param1': ParameterDefinition(default_value=10, description='Parameter 1'),
            # More parameters...
        },
        inputs={
            'input1': PortDefinition(type=PortType.INT, description='Input 1'),
            # More inputs...
        },
        outputs={
            'output1': PortDefinition(type=PortType.FLOAT, description='Output 1'),
            # More outputs...
        },
        methods={
            'process_data': MethodDefinition(
                description='Process the input data',
                inputs=['input1'],
                outputs=['output1']
            ),
            # More methods...
        }
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step(
            "process_data",
            self.process_data,
            method_key="process_data"
        )

    def process_data(self, input1: int) -> Dict[str, float]:
        # Process the input and return the output
        result = float(input1) * self._parameters['param1']
        return {'output1': result}
```

## Example Node Implementation

Here's a simplified example of a spike analysis node:

```python
class SpikeAnalysisNode(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type='spike_analysis',
        description='Analyzes spike trains from neural simulations',

        parameters={
            'time_window': ParameterDefinition(
                default_value=[0.0, 1000.0],
                description='Time window for analysis in milliseconds',
                constraints={'min_length': 2, 'max_length': 2}
            ),
            'bin_size': ParameterDefinition(
                default_value=10.0,
                description='Bin size for spike histograms in milliseconds',
                constraints={'min': 0.1, 'max': 1000.0},
                optimizable=True,
                optimization_range=[1.0, 50.0]
            ),
            'detection_threshold': ParameterDefinition(
                default_value=0.5,
                description='Threshold for spike detection',
                constraints={'min': 0.1, 'max': 0.9},
                optimizable=True,
                optimization_range=[0.2, 0.8]
            )
        },

        inputs={
            'spike_data': PortDefinition(
                type=PortType.OBJECT,
                description='Spike recorder data from simulation'
            )
        },

        outputs={
            'firing_rates': PortDefinition(
                type=PortType.DICT,
                description='Firing rates for each neuron'
            )
        },

        methods={
            'calculate_rates': MethodDefinition(
                description='Calculate firing rates',
                inputs=['spike_data'],
                outputs=['firing_rates']
            )
        }
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step(
            "calculate_rates",
            self.calculate_rates,
            method_key="calculate_rates"
        )

    def calculate_rates(self, spike_data: Dict[str, Any]) -> Dict[str, Dict[int, float]]:
        # Implementation of firing rate calculation
        # ...
        return {'firing_rates': calculated_rates}
```

This node schema provides a flexible yet structured way to define processing components for neural simulations, ensuring type safety and proper data flow between workflow elements.
