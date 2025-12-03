# NeuroWorkflow Architecture Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Vision and Goals](#vision-and-goals)
3. [High-Level Architecture](#high-level-architecture)
4. [Component Architecture](#component-architecture)
5. [Data Flow](#data-flow)
6. [Module Documentation](#module-documentation)
7. [Schema Reference](#schema-reference)
8. [Extension Points](#extension-points)
9. [Interactions Between Components](#interactions-between-components)

---

## System Overview

NeuroWorkflow is a Python-based framework for building and executing neural simulation workflows. It provides a node-based architecture where computational steps are represented as nodes that can be connected to form complex processing pipelines.

### Core Principles

1. **Modularity**: Each processing step is a self-contained node
2. **Type Safety**: Ports are typed to ensure correct data flow
3. **Extensibility**: Easy to add custom nodes and functionality
4. **Interoperability**: Support for multiple simulation backends (NEST, TVB, SONATA)
5. **AI-Ready**: Parameter descriptions act as prompts for metadata retrieval
6. **HPC-Ready**: Support for job submission to HPC systems

---

## Vision and Goals

### Vision

To create an open-source, globally accessible, easy-to-use framework for building digital brain models that:
- Enables researchers to easily construct complex neural simulation workflows
- Supports integration with diverse neuroscience databases and tools
- Facilitates collaboration and reproducibility
- Provides AI-assisted parameter discovery and optimization
- Scales from local development to HPC supercomputers

### Goals

1. **Scientific Community Support**: Provide tools that researchers understand and can integrate with their own work
2. **Open Source & No Cost**: Freely available to the global scientific community
3. **Python-Based**: Everything in Python for ease of use and maintenance
4. **Easy to Use**: Intuitive graphical interface and Python API
5. **Easy to Maintain**: Clean architecture and comprehensive documentation
6. **HPC Integration**: Support for submitting jobs to various HPC systems (Fugaku, AWS, Google Cloud, etc.)
7. **Metadata Integration**: Connect node parameters with external databases for parameter discovery

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
├──────────────────────┬──────────────────┬───────────────────────┤
│   Web UI (React)     │  Python API      │   Jupyter Notebooks    │
│   - Visual Editor    │  - Programmatic  │   - Interactive        │
│   - Node Management  │    Workflows      │   - Exploration        │
└──────────┬──────────┴────────┬─────────┴──────────┬────────────┘
           │                    │                    │
           └────────────────────┼────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│                    Backend Services                           │
├──────────────────────┬──────────────────┬─────────────────────┤
│  Django REST API     │  JupyterHub      │   MCP Server        │
│  - Workflow CRUD     │  - Notebook      │   - LLM Integration  │
│  - Node Management   │    Execution      │   - Workflow Proxy   │
│  - Code Generation   │  - NEST Simulator │                     │
└──────────┬───────────┴──────────┬───────┴─────────────────────┘
           │                       │
           └───────────┬───────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                  Core Library (neuroworkflow)                 │
├────────────────────────────────────────────────────────────────┤
│  • Node System      • Workflow Execution  • Script Generation  │
│  • Port System      • Parameter Schema    • Job Management     │
│  • Schema Defs      • Metadata Service    • SnakeMake Export   │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│              Simulation Backends                               │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│  NEST        │  TVB         │  SONATA      │  Custom         │
│  Simulator   │  (Virtual    │  Networks    │  Backends       │
│              │   Brain)     │              │                 │
└──────────────┴──────────────┴──────────────┴──────────────────┘
```

---

## Component Architecture

### 1. Core Library (`src/neuroworkflow/`)

The core library provides the fundamental building blocks for workflows.

#### 1.1 Core Module (`core/`)

**`node.py`**: Base `Node` class
- Defines the interface for all workflow nodes
- Manages ports, parameters, and process steps
- Handles node execution lifecycle

**`port.py`**: Port system
- `InputPort` and `OutputPort` classes
- Type checking and validation
- Data flow management

**`schema.py`**: Schema definitions
- `NodeDefinitionSchema`: Node structure definition
- `ParameterDefinition`: Parameter metadata
- `PortDefinition`: Port type definitions
- `ResourceRequirements`: HPC resource specs
- `PortType` enum: Memory and I/O port types

**`workflow.py`**: Workflow execution
- `Workflow` class: Represents a complete workflow
- `WorkflowBuilder`: Builder pattern for creating workflows
- Execution order computation
- Dependency resolution

#### 1.2 Nodes Module (`nodes/`)

Organized by category:
- **`network/`**: Network building nodes (populations, connections)
- **`simulation/`**: Simulation execution nodes
- **`stimulus/`**: Stimulus generation nodes
- **`analysis/`**: Analysis and visualization nodes
- **`optimization/`**: Parameter optimization nodes
- **`io/`**: Input/output nodes

Each node:
- Inherits from `Node` base class
- Defines `NODE_DEFINITION` schema
- Implements process steps (validation, execution, code generation)

#### 1.3 Utils Module (`utils/`)

**`script_exporter.py`**: Script generation
- Export workflows as Python scripts
- Export as Jupyter notebooks
- Export as SnakeMake workflows (new)

**`snakemake_generator.py`**: SnakeMake workflow generation
- Converts execution sequence to SnakeMake rules
- Generates Snakefile and config.yaml
- Supports HPC job submission

**`job_managers/`**: HPC job management
- `base.py`: Abstract `JobManager` interface
- `slurm.py`: SLURM job manager implementation
- Extensible for other job schedulers (PBS, AWS Batch, etc.)

**`parameter_metadata_service.py`**: Parameter metadata
- Interface for querying external databases
- Species-specific parameter retrieval
- Parameter suggestion engine

#### 1.4 CLI Module (`cli/`)

Command-line interface for workflow execution.

---

### 2. Backend (`gui/workflow_backend/`)

Django-based REST API server.

#### 2.1 Django Project Structure

**`app/workflow/`**: Workflow management
- `models.py`: Database models (FlowProject, FlowNode, FlowEdge)
- `views.py`: REST API views
- `code_generation_service.py`: Code generation from React Flow JSON
- `urls.py`: URL routing

**`app/box/`**: Node management
- `models.py`: PythonFile model (stores node definitions)
- `views.py`: Node upload, list, sync endpoints
- `urls.py`: URL routing

**`app/auth/`**: Authentication
- Supabase integration
- User management

**`config/`**: Django configuration
- `settings.py`: Django settings
- `urls.py`: Main URL configuration

#### 2.2 Key Features

- REST API for workflow CRUD operations
- Node synchronization from file system
- Batch code generation from visual workflows
- JupyterHub integration for notebook execution

---

### 3. Frontend (`gui/workflow_frontend/`)

React-based web application.

#### 3.1 Technology Stack

- **React** with TypeScript
- **React Flow** for visual workflow editor
- **Chakra UI** for components
- **Vite** for build tooling
- **Aspida** for API client generation

#### 3.2 Key Components

**`views/home/`**: Main workflow editor
- `homeView.tsx`: Main editor interface
- `components/nodeDetailModal.tsx`: Node parameter editing
- `components/projectSelector.tsx`: Project selection
- `components/edgeMenu.tsx`: Edge configuration

**`api/`**: API client
- Auto-generated from OpenAPI schema
- Type-safe API calls

**`auth/`**: Authentication
- Supabase client integration
- Protected routes

---

### 4. JupyterHub Integration

- Spawns Docker containers with NEST simulator
- Provides isolated execution environments
- Mounts project directories for persistence
- Integrated with workflow execution

---

### 5. MCP Server

Model Context Protocol server for LLM integration.
- Provides workflow management via MCP
- Enables AI assistants to interact with workflows
- Proxy to Django backend API

---

## Data Flow

### Workflow Execution Flow

```
1. User creates workflow (Web UI or Python API)
   ↓
2. Workflow stored in database (Django)
   ↓
3. User executes workflow
   ↓
4. WorkflowBuilder computes execution order
   ↓
5. For each node in order:
   a. Validate parameters
   b. Execute process steps
   c. Generate Python script (if requested)
   d. Update output ports
   ↓
6. Execution sequence tracked
   ↓
7. Scripts exported (Python/Notebook/SnakeMake)
   ↓
8. Results available for analysis
```

### Node Processing Pipeline

```
Node.process()
  ↓
1. validate_parameters()
   - Check constraints
   - Apply defaults
   - Query metadata (if enabled)
   ↓
2. Execute process steps in order:
   - Each step calls a method
   - Methods read from input ports
   - Methods write to output ports
   ↓
3. generate_python_script() (if requested)
   - Create executable Python code
   - Include imports and setup
   ↓
4. Return success/failure
```

### API Request Flow

```
Frontend (React)
  ↓ HTTP Request
Backend (Django REST API)
  ↓
View/ViewSet
  ↓
Service Layer (CodeGenerationService, etc.)
  ↓
Core Library (neuroworkflow)
  ↓
Response
  ↓ HTTP Response
Frontend
```

---

## Module Documentation

### Core Modules

#### `neuroworkflow.core.node`
- **Node**: Base class for all workflow nodes
- **ProcessStep**: Represents a single processing step within a node

#### `neuroworkflow.core.workflow`
- **Workflow**: Complete workflow with nodes and connections
- **WorkflowBuilder**: Builder for creating workflows programmatically
- **Connection**: Represents a connection between node ports

#### `neuroworkflow.core.schema`
- **NodeDefinitionSchema**: Complete node definition
- **ParameterDefinition**: Parameter with metadata support
- **PortDefinition**: Port type and description
- **ResourceRequirements**: HPC resource specifications
- **PortType**: Enum of port types (memory and I/O)

#### `neuroworkflow.core.port`
- **InputPort**: Input data port
- **OutputPort**: Output data port
- Port validation and type checking

### Utility Modules

#### `neuroworkflow.utils.script_exporter`
- `export_workflow_scripts()`: Main export function
- Supports Python, Jupyter notebook, and SnakeMake formats

#### `neuroworkflow.utils.snakemake_generator`
- `generate_snakemake_workflow()`: Generate SnakeMake workflow
- Converts nodes to SnakeMake rules
- Handles file-based I/O ports

#### `neuroworkflow.utils.job_managers`
- `JobManager`: Abstract base class
- `SLURMJobManager`: SLURM implementation
- Extensible for other job schedulers

#### `neuroworkflow.utils.parameter_metadata_service`
- `ParameterMetadataService`: Query external databases
- `ParameterSuggestion`: Suggested parameter values
- Species-specific parameter retrieval

---

## Schema Reference

### NodeDefinitionSchema

```python
@dataclass
class NodeDefinitionSchema:
    type: str                    # Unique node type identifier
    description: str            # Human-readable description
    parameters: Dict[str, ...]   # Parameter definitions
    inputs: Dict[str, ...]       # Input port definitions
    outputs: Dict[str, ...]      # Output port definitions
    methods: Dict[str, ...]       # Method definitions
```

### ParameterDefinition

```python
@dataclass
class ParameterDefinition:
    default_value: Any                          # Default parameter value
    description: str                           # Description (acts as prompt)
    constraints: Dict[str, Any]                # Validation constraints
    optimizable: bool                           # Can be optimized
    optimization_range: Optional[List[Any]]   # Optimization range
    metadata_sources: List[str]                 # Available metadata sources
    species_specific: bool                      # Varies by species
    suggested_values: List[Dict[str, Any]]      # AI/metadata suggestions
```

### PortDefinition

```python
@dataclass
class PortDefinition:
    type: Union[PortType, Type]  # Port data type
    description: str             # Port description
    optional: bool              # Is port optional
```

### ResourceRequirements

```python
@dataclass
class ResourceRequirements:
    cpus: int                    # Number of CPUs
    memory_gb: float            # Memory in GB
    gpus: int                   # Number of GPUs
    walltime_hours: float       # Maximum execution time
    queue: Optional[str]        # Job queue name
    account: Optional[str]      # Account/project name
    nodes: int                  # Number of compute nodes
    tasks_per_node: int        # Tasks per node (MPI)
```

---

## Extension Points

### Creating Custom Nodes

1. Inherit from `Node` base class
2. Define `NODE_DEFINITION` schema
3. Implement process steps
4. Optionally implement `generate_python_script()`

See `CUSTOM_NODE_TUTORIAL.md` for detailed guide.

### Adding Job Managers

1. Inherit from `JobManager` base class
2. Implement abstract methods:
   - `generate_job_script()`
   - `submit_job()`
   - `get_job_status()`
   - `get_job_info()`
3. Register in `job_managers/__init__.py`

### Integrating External Databases

1. Extend `ParameterMetadataService`
2. Implement query methods for your database
3. Register as a metadata source
4. Update `MetadataSource` enum

### Adding Script Export Formats

1. Create generator function in `utils/`
2. Add export option to `export_workflow_scripts()`
3. Handle format-specific requirements

---

## Interactions Between Components

### Core Library ↔ Backend

- Backend uses core library for:
  - Code generation from workflows
  - Node validation
  - Workflow execution
- Core library is independent (no Django dependencies)

### Backend ↔ Frontend

- REST API communication
- JSON serialization of workflows
- Real-time updates (future: WebSockets)

### Frontend ↔ JupyterHub

- Frontend requests notebook creation
- JupyterHub spawns container
- Notebooks execute workflows

### Core Library ↔ Simulation Backends

- Nodes interact with simulation backends (NEST, TVB, SONATA)
- Backends are loaded as Python modules
- No tight coupling - backends can be swapped

### Metadata Service ↔ External Databases

- Service queries external APIs/databases
- Returns parameter suggestions
- Can be extended with new sources

---

## Future Architecture Considerations

### GraphQL Interface
- Contractors working on GraphQL API
- Will provide alternative to REST API
- Enables more flexible queries

### Resource Discovery
- Automatic detection of available HPC resources
- Dynamic resource allocation
- Integration with cluster management systems

### Format Adapters
- Convert between model formats (SONATA, NeuroML, etc.)
- Preserve context while standardizing
- Enable interoperability

### AI Agent Integration
- LLM agents for workflow creation
- Parameter suggestion and optimization
- Natural language workflow descriptions

---

*Last Updated: November 2025*



