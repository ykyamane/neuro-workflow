# Node Management Guide

This guide explains how to add, view, and use custom nodes in the NeuroWorkflow system.

## Overview

The NeuroWorkflow system allows you to add custom Python nodes that can be used in workflow builders. Nodes are stored in the `codes/nodes/` directory and organized by category.

## Directory Structure

Nodes are organized in the following structure:

```
gui/workflow_backend/django-project/codes/nodes/
├── __init__.py
├── analysis/          # Analysis nodes
│   ├── __init__.py
│   ├── SpikeAnalysisNode.py
│   └── TVBVisualizationNode.py
├── io/                # Input/Output nodes
│   └── __init__.py
├── network/           # Network building nodes
│   ├── __init__.py
│   ├── BuildSonataNetworkNode.py
│   ├── NESTNeuronSetupNode.py
│   └── ...
├── optimization/       # Optimization nodes
│   ├── __init__.py
│   └── JointOptimizationNode.py
├── simulation/        # Simulation nodes
│   ├── __init__.py
│   ├── NeuronSimulationNode.py
│   └── ...
└── stimulus/          # Stimulus nodes
    ├── __init__.py
    ├── StimulusGeneratorNode.py
    └── ...
```

## Available Categories

The system supports these node categories:
- **analysis** - Analysis nodes
- **io** - Input/Output nodes
- **network** - Network building nodes
- **optimization** - Optimization nodes
- **simulation** - Simulation nodes
- **stimulus** - Stimulus nodes

## How to Add Nodes

There are **three ways** to add nodes to the system:

### Method 1: Upload via Web UI (Recommended)

1. **Start the system**:
   ```bash
   cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui
   docker-compose up
   ```

2. **Access the Web UI**: Open `http://localhost:5173` in your browser

3. **Upload a node file**:
   - Use the file upload interface in the Web UI
   - Select a Python file containing a node class
   - Choose the appropriate category
   - The system will automatically:
     - Parse the node definition
     - Extract parameters, inputs, outputs, and methods
     - Save it to the database
     - Copy it to the appropriate `codes/nodes/{category}/` folder

### Method 2: Create Files Directly in the Folder

1. **Navigate to the nodes directory**:
   ```bash
   cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui/workflow_backend/django-project/codes/nodes
   ```

2. **Choose or create a category folder**:
   ```bash
   # Use existing category
   cd analysis
   
   # Or create a new category (if needed)
   mkdir my_category
   cd my_category
   ```

3. **Create your node file** (e.g., `MyCustomNode.py`):
   ```python
   from neuroworkflow.core.node import Node
   from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition
   from neuroworkflow.core.port import PortType

   class MyCustomNode(Node):
       """My custom node description."""
       
       NODE_DEFINITION = NodeDefinitionSchema(
           type='my_custom_type',
           description='Description of what this node does',
           parameters={
               'param1': ParameterDefinition(
                   default_value=10,
                   description='First parameter'
               ),
           },
           inputs={
               'input1': PortDefinition(
                   type=PortType.OBJECT,
                   description='Input data'
               ),
           },
           outputs={
               'output1': PortDefinition(
                   type=PortType.DICT,
                   description='Output data'
               ),
           },
       )
       
       def process(self):
           """Process method implementation."""
           # Your node logic here
           result = self._parameters['param1']
           return {'output1': result}
   ```

4. **Sync the file to the database** (see Method 3 below)

### Method 3: Bulk Sync Existing Files

If you have existing node files in the `codes/nodes/` folder that aren't in the database:

1. **Use the bulk sync API endpoint**:
   ```bash
   curl -X POST http://localhost:3000/api/box/sync/
   ```

   Or use the Web UI if there's a sync button available.

2. **What it does**:
   - Scans all `.py` files in `codes/nodes/{category}/` folders
   - Analyzes each file for node classes
   - Adds them to the database if they don't already exist
   - Skips files that are already registered

## Node File Requirements

For a Python file to be recognized as a node, it must:

1. **Contain a class that inherits from `Node`**:
   ```python
   from neuroworkflow.core.node import Node
   
   class MyNode(Node):
       ...
   ```

2. **Define `NODE_DEFINITION`**:
   ```python
   NODE_DEFINITION = NodeDefinitionSchema(
       type='node_type',
       description='Node description',
       parameters={...},
       inputs={...},
       outputs={...},
       methods={...},  # Optional
   )
   ```

3. **Implement processing methods** as defined in the methods section

## How Nodes Are Analyzed

When you upload or sync a node file, the system automatically:

1. **Parses the Python file** using AST (Abstract Syntax Tree)
2. **Extracts the `NODE_DEFINITION`** schema
3. **Identifies**:
   - Node class name
   - Description
   - Parameters (with types, defaults, constraints)
   - Input ports (with types and descriptions)
   - Output ports (with types and descriptions)
   - Methods (with inputs/outputs)
4. **Stores** the information in the database
5. **Makes it available** in the Web UI workflow builder

## Viewing Available Nodes

### Via Web UI

1. Open `http://localhost:5173`
2. In the workflow builder, nodes should appear in the node palette
3. Uploaded nodes will be marked as "uploadedNode" type

### Via API

**Get all uploaded nodes**:
```bash
curl http://localhost:3000/api/box/uploaded-nodes/
```

**Get all files**:
```bash
curl http://localhost:3000/api/box/files/
```

**Get files by category**:
```bash
curl "http://localhost:3000/api/box/files/?category=analysis"
```

**Get categories**:
```bash
curl http://localhost:3000/api/box/categories/
```

## Using Nodes in Workflows

Once nodes are added and analyzed:

1. **In the Web UI**:
   - Nodes appear in the node palette
   - Drag and drop them onto the canvas
   - Configure parameters in the node properties panel
   - Connect inputs and outputs between nodes

2. **In generated code**:
   - When you generate workflow code, nodes are imported from:
     ```python
     from nodes.{category}.{ClassName} import {ClassName}
     ```
   - Example:
     ```python
     from nodes.network.BuildSonataNetworkNode import BuildSonataNetworkNode
     ```

## Editing Node Files

### Via Web UI

1. Access the code editor in the Web UI
2. Edit the node file content
3. Save changes
4. The system will:
   - Update the database
   - Update the physical file in `codes/nodes/{category}/`
   - Re-analyze the node

### Via File System

1. Edit the file directly:
   ```bash
   cd /Users/kirill/Documents/digital_brain/neuro-workflow/gui/workflow_backend/django-project/codes/nodes/analysis
   nano MyCustomNode.py
   ```

2. **Re-sync** to update the database:
   ```bash
   curl -X POST http://localhost:3000/api/box/sync/
   ```

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/box/upload/` | POST | Upload a new node file |
| `/api/box/files/` | GET | List all uploaded files |
| `/api/box/files/<id>/` | GET | Get file details |
| `/api/box/files/<id>/` | DELETE | Delete a file |
| `/api/box/uploaded-nodes/` | GET | Get all analyzed nodes (for frontend) |
| `/api/box/files/<filename>/code/` | GET | Get file source code |
| `/api/box/files/<filename>/code/` | PUT | Update file source code |
| `/api/box/copy/` | POST | Copy a file |
| `/api/box/sync/` | POST | Bulk sync files from `codes/nodes/` folder |
| `/api/box/categories/` | GET | Get available categories |

## Example: Creating a Simple Analysis Node

Here's a complete example of creating a custom analysis node:

```python
"""
Example: Simple Data Filter Node
"""
from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition
)
from neuroworkflow.core.port import PortType

class DataFilterNode(Node):
    """Filters data based on a threshold value."""
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='data_filter',
        description='Filters numerical data based on a threshold',
        parameters={
            'threshold': ParameterDefinition(
                default_value=0.5,
                description='Threshold value for filtering',
                constraints={'min': 0, 'max': 1}
            ),
            'filter_type': ParameterDefinition(
                default_value='greater',
                description='Filter type: greater, less, or equal'
            ),
        },
        inputs={
            'data': PortDefinition(
                type=PortType.LIST,
                description='Input data list to filter'
            ),
        },
        outputs={
            'filtered_data': PortDefinition(
                type=PortType.LIST,
                description='Filtered output data'
            ),
            'count': PortDefinition(
                type=PortType.INT,
                description='Number of items that passed the filter'
            ),
        },
        methods={
            'filter': MethodDefinition(
                description='Filter the input data',
                inputs=['data'],
                outputs=['filtered_data', 'count']
            ),
        },
    )
    
    def _define_process_steps(self):
        """Define process steps linking methods to node definition."""
        self.add_process_step(
            name='filter',
            method=self.filter_data,
            description='Filter data based on threshold',
            inputs=['data'],
            outputs=['filtered_data', 'count'],
            method_key='filter'
        )
    
    def filter_data(self):
        """Filter data based on threshold."""
        data = self._input_ports['data'].get_value()
        threshold = self._parameters['threshold']
        filter_type = self._parameters['filter_type']
        
        if filter_type == 'greater':
            filtered = [x for x in data if x > threshold]
        elif filter_type == 'less':
            filtered = [x for x in data if x < threshold]
        else:  # equal
            filtered = [x for x in data if x == threshold]
        
        return {
            'filtered_data': filtered,
            'count': len(filtered)
        }
```

**To add this node**:

1. Save it as `DataFilterNode.py` in `codes/nodes/analysis/`
2. Sync it:
   ```bash
   curl -X POST http://localhost:3000/api/box/sync/
   ```
3. Or upload it via the Web UI

## Troubleshooting

### Node not appearing in UI

1. **Check if it's analyzed**:
   ```bash
   curl http://localhost:3000/api/box/files/ | jq '.[] | select(.name=="YourNode.py")'
   ```
   Look for `"is_analyzed": true`

2. **Check for analysis errors**:
   ```bash
   curl http://localhost:3000/api/box/files/ | jq '.[] | select(.name=="YourNode.py") | .analysis_error'
   ```

3. **Re-sync the file**:
   ```bash
   curl -X POST http://localhost:3000/api/box/sync/
   ```

### Node definition not recognized

- Ensure `NODE_DEFINITION` is a class attribute (not instance)
- Check that it uses `NodeDefinitionSchema`
- Verify all imports are correct
- Check the file syntax is valid Python

### File not syncing

- Ensure the file is in the correct category folder
- Check file has `.py` extension
- Verify the file contains a class inheriting from `Node`
- Check Django logs for errors

## Best Practices

1. **Organize by category**: Place nodes in appropriate category folders
2. **Use descriptive names**: Node class names should be clear and descriptive
3. **Document well**: Add comprehensive descriptions to parameters, inputs, and outputs
4. **Test locally**: Test your node code before uploading
5. **Version control**: Keep your node files in version control
6. **Follow conventions**: Use the same structure as existing nodes

## Next Steps

- See `CUSTOM_NODE_TUTORIAL.md` for detailed node creation guide
- See `NODE_SCHEMA.md` for complete schema documentation
- Check existing nodes in `codes/nodes/` for examples


