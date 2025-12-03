# NeuroWorkflow Development Roadmap
## Analysis of Meeting Transcription - Actionable Items

This document analyzes the meeting transcription and identifies concrete, codebase-related improvements that can be implemented in the NeuroWorkflow system.

---

## 1. Parameter Metadata Connection System

### Current State
- Nodes have parameters with `name` and `description` fields (see `ParameterDefinition` in `src/neuroworkflow/core/schema.py`)
- Parameters are defined in `NODE_DEFINITION.parameters` dictionary
- Each parameter has a `description` field that acts as a "prompt" for AI/metadata retrieval

### Requirements from Meeting
1. **Connect node parameters to external databases** (open source databases, papers, graphs)
2. **Query parameters for different species** (mouse, monkey, human)
3. **Retrieve parameter values from diverse data sources** based on parameter descriptions
4. **Support intermediate state** - suggest parameter values rather than directly setting them
5. **Human-in-the-loop mapping** - allow manual review/approval of suggested values

### Implementation Tasks

#### 1.1 Create Parameter Metadata Service
**Location**: `src/neuroworkflow/utils/parameter_metadata_service.py` (new file)

**Features**:
- Interface for querying external databases
- Support for multiple data sources (Allen Brain Atlas, NeuroMorpho, etc.)
- Species-specific parameter retrieval
- Parameter suggestion engine based on descriptions

**API Design**:
```python
class ParameterMetadataService:
    def suggest_parameter_values(
        self, 
        parameter_name: str, 
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[ParameterSuggestion]:
        """
        Query external databases and return suggested parameter values.
        Returns suggestions with confidence scores and source information.
        """
        pass
    
    def get_species_specific_parameters(
        self,
        node_type: str,
        species: str
    ) -> Dict[str, Any]:
        """
        Get species-specific parameter values for a node type.
        """
        pass
```

#### 1.2 Extend ParameterDefinition Schema
**Location**: `src/neuroworkflow/core/schema.py`

**Changes**:
- Add `metadata_sources: List[str]` field to `ParameterDefinition`
- Add `species_specific: bool` flag
- Add `suggestions: List[Dict]` field for storing AI-suggested values

#### 1.3 Add Metadata Query Endpoint
**Location**: `gui/workflow_backend/django-project/app/box/views.py` or new `app/metadata/views.py`

**Endpoint**: `GET /api/metadata/parameters/suggest/`
- Query parameters: `parameter_name`, `description`, `species`, `node_type`
- Returns: List of suggested values with sources and confidence scores

#### 1.4 Frontend Integration
**Location**: `gui/workflow_frontend/src/views/home/components/nodeDetailModal.tsx`

**Features**:
- "Suggest Values" button for each parameter
- Display suggested values with source attribution
- Allow user to accept/reject suggestions
- Show intermediate state (suggested but not applied)

---

## 2. HPC/Job Management System

### Current State
- Scripts are generated as Python files (see `src/neuroworkflow/utils/script_exporter.py`)
- No HPC job submission capability
- No resource management (CPU, memory, GPU selection)

### Requirements from Meeting
1. **Support multiple job managers**: SLURM, Sbatch, PBS, etc.
2. **Submit jobs to different servers**: Google Cloud, AWS, local HPC, Fugaku supercomputer
3. **Generate SnakeMake scripts** in addition to Python scripts
4. **Resource management**: Read available resources and select CPUs/memory/GPU
5. **Job submission interface**: Open source graphical interface for job management

### Implementation Tasks

#### 2.1 Create Job Manager Abstraction
**Location**: `src/neuroworkflow/utils/job_managers/` (new directory)

**Structure**:
```
job_managers/
├── __init__.py
├── base.py          # Abstract base class
├── slurm.py         # SLURM job manager
├── sbatch.py        # Sbatch job manager
├── pbs.py           # PBS/Torque job manager
├── aws_batch.py     # AWS Batch
└── google_cloud.py   # Google Cloud Jobs
```

**Base Interface**:
```python
class JobManager(ABC):
    @abstractmethod
    def generate_job_script(
        self,
        python_script: str,
        resources: ResourceRequirements,
        job_name: str
    ) -> str:
        """Generate job submission script."""
        pass
    
    @abstractmethod
    def submit_job(self, job_script_path: str) -> str:
        """Submit job and return job ID."""
        pass
    
    @abstractmethod
    def get_job_status(self, job_id: str) -> JobStatus:
        """Get current job status."""
        pass
```

#### 2.2 Resource Requirements Schema
**Location**: `src/neuroworkflow/core/schema.py` (extend)

**Add**:
```python
@dataclass
class ResourceRequirements:
    cpus: int = 1
    memory_gb: float = 4.0
    gpus: int = 0
    walltime_hours: float = 1.0
    queue: Optional[str] = None
    account: Optional[str] = None
```

#### 2.3 SnakeMake Script Generator
**Location**: `src/neuroworkflow/utils/snakemake_generator.py` (new file)

**Features**:
- Convert workflow execution sequence to SnakeMake workflow
- Generate `Snakefile` with rules for each node
- Support file-based I/O ports (already defined in `PortType`)
- Generate job submission scripts for HPC

**API**:
```python
def generate_snakemake_workflow(
    execution_sequence: Dict[str, Any],
    output_dir: str = "./output",
    job_manager: Optional[JobManager] = None
) -> Dict[str, str]:
    """
    Generate SnakeMake workflow from execution sequence.
    Returns paths to Snakefile and config files.
    """
    pass
```

#### 2.4 Extend Script Exporter
**Location**: `src/neuroworkflow/utils/script_exporter.py`

**Changes**:
- Add `export_snakemake: bool` parameter to `export_workflow_scripts()`
- Add `job_manager_type: Optional[str]` parameter
- Add `resource_requirements: Optional[ResourceRequirements]` parameter
- Integrate with SnakeMake generator

#### 2.5 Resource Discovery Service
**Location**: `src/neuroworkflow/utils/resource_discovery.py` (new file)

**Features**:
- Query available resources on HPC systems
- Detect available CPUs, memory, GPUs
- Suggest optimal resource allocation based on workflow requirements

**Note**: This requires appropriate permissions/configuration on the target system.

#### 2.6 Backend API for Job Submission
**Location**: `gui/workflow_backend/django-project/app/workflow/views.py` (extend)

**New Endpoints**:
- `POST /api/workflow/{workflow_id}/generate-job-script/` - Generate job submission script
- `POST /api/workflow/{workflow_id}/submit-job/` - Submit job to HPC
- `GET /api/workflow/{workflow_id}/job-status/{job_id}/` - Get job status
- `GET /api/workflow/{workflow_id}/available-resources/` - Query available resources

#### 2.7 Frontend Job Management UI
**Location**: `gui/workflow_frontend/src/views/home/components/` (new component)

**New Component**: `JobSubmissionModal.tsx`

**Features**:
- Select job manager type (SLURM, Sbatch, etc.)
- Configure resource requirements (CPUs, memory, GPU)
- Select target server/environment
- Submit job and monitor status
- View job logs and results

---

## 3. GraphQL Interface

### Current State
- REST API only (Django REST Framework)
- No GraphQL implementation found in codebase
- Meeting mentions "GraphQL interface is ongoing" with contractors

### Requirements from Meeting
- GraphQL interface for querying workflow data
- Contractors working on this until January/February

### Implementation Tasks

#### 3.1 Install GraphQL Dependencies
**Location**: `gui/workflow_backend/django-project/` (update `pyproject.toml` or `requirements.txt`)

**Packages**:
- `graphene-django` - Django GraphQL integration
- `graphene` - GraphQL library

#### 3.2 Create GraphQL Schema
**Location**: `gui/workflow_backend/django-project/app/workflow/schema.py` (new file)

**Schema Types**:
- `WorkflowType` - Query workflows
- `NodeType` - Query nodes
- `ParameterType` - Query parameters
- `ExecutionSequenceType` - Query execution history

#### 3.3 GraphQL Endpoint
**Location**: `gui/workflow_backend/django-project/config/urls.py`

**Add**: GraphQL endpoint (typically `/graphql/`)

#### 3.4 Frontend GraphQL Client
**Location**: `gui/workflow_frontend/src/api/` (new file)

**Package**: `@apollo/client` or `graphql-request`

---

## 4. Architecture Documentation

### Current State
- Basic README files exist
- Some tutorial/guide documents (CUSTOM_NODE_TUTORIAL.md, NODE_SCHEMA.md)
- No comprehensive architecture documentation

### Requirements from Meeting
- **Comprehensive documentation** covering:
  - Direction, goals, targets, vision
  - Implementation details
  - System architecture
  - Elements, modules, libraries, workflows, schemas
  - Interactions between parts
  - Global vision

### Implementation Tasks

#### 4.1 Create Architecture Documentation
**Location**: `docs/ARCHITECTURE.md` (new file)

**Sections**:
1. **System Overview**
   - Vision and goals
   - High-level architecture diagram
   - Core principles

2. **Component Architecture**
   - Core library (`src/neuroworkflow/`)
   - Backend (Django)
   - Frontend (React)
   - JupyterHub integration
   - MCP server

3. **Data Flow**
   - Workflow execution flow
   - Node processing pipeline
   - Script generation process
   - API request/response flow

4. **Module Documentation**
   - `core/` - Node, Workflow, Port, Schema
   - `nodes/` - Node implementations by category
   - `utils/` - Utility functions
   - `cli/` - Command-line interface

5. **Schema Reference**
   - NodeDefinitionSchema
   - ParameterDefinition
   - PortDefinition
   - Workflow structure

6. **Extension Points**
   - Creating custom nodes
   - Adding new job managers
   - Integrating external databases
   - Adding new script formats

#### 4.2 API Documentation
**Location**: `docs/API.md` (new file)

**Content**:
- REST API endpoints (complete reference)
- Request/response examples
- Authentication
- Error handling
- GraphQL schema (when implemented)

#### 4.3 Development Guide
**Location**: `docs/DEVELOPMENT.md` (new file)

**Content**:
- Setup development environment
- Code structure and conventions
- Testing guidelines
- Contribution workflow
- Deployment process

---

## 5. Standardization and Interoperability

### Requirements from Meeting
- **Standardized rules** between different models/formats
- **Preserve context/details** of specific file formats/models
- **Intermediate state** for parameter mapping

### Implementation Tasks

#### 5.1 Format Adapter System
**Location**: `src/neuroworkflow/utils/adapters/` (new directory)

**Purpose**: Convert between different model formats while preserving context

**Structure**:
```
adapters/
├── __init__.py
├── base.py           # Abstract adapter
├── sonata.py         # SONATA format adapter
├── neuroml.py        # NeuroML adapter
├── nest.py           # NEST-specific formats
└── registry.py       # Adapter registry
```

#### 5.2 Metadata Preservation
**Location**: Extend node execution to preserve format-specific metadata

**Changes**:
- Store original format metadata in node context
- Include metadata in generated scripts
- Support format-specific parameter constraints

---

## 6. Integration with Existing Tools

### Requirements from Meeting
- Integrate open source libraries/applications doing similar things
- Learn from existing solutions (Brain Modeling Toolkit, Virtual Brain, CobraWeb, BRATH2)
- Build better architecture from existing solutions

### Implementation Tasks

#### 6.1 Comparative Analysis Document
**Location**: `docs/COMPARATIVE_ANALYSIS.md` (new file)

**Content**:
- Analysis of similar tools
- Feature comparison
- Integration opportunities
- Best practices to adopt

#### 6.2 Integration Adapters
**Location**: `src/neuroworkflow/integrations/` (new directory)

**Purpose**: Adapters for integrating with external tools

**Examples**:
- Allen Brain Atlas API
- NeuroMorpho database
- Virtual Brain Toolkit
- Other neuroscience databases

---

## Priority Recommendations

### High Priority (Immediate Value)
1. **Parameter Metadata Service** (Section 1) - Core feature for AI-assisted workflow creation
2. **SnakeMake Script Generation** (Section 2.3) - Enables HPC workflows
3. **Architecture Documentation** (Section 4) - Essential for development and onboarding

### Medium Priority (Important but Complex)
1. **HPC Job Management** (Section 2) - Requires infrastructure setup
2. **GraphQL Interface** (Section 3) - Already in progress with contractors
3. **Resource Discovery** (Section 2.5) - Depends on HPC access

### Low Priority (Future Enhancements)
1. **Format Adapters** (Section 5) - Can be added incrementally
2. **External Tool Integration** (Section 6) - Research and analysis phase

---

## Implementation Notes

### Dependencies to Add
- `graphene-django` - For GraphQL
- `snakemake` - For SnakeMake script generation
- `pyslurm` or `subprocess` - For SLURM job management
- `boto3` - For AWS integration
- `google-cloud-batch` - For Google Cloud integration

### Configuration Requirements
- HPC system access credentials
- Database connection strings for metadata sources
- API keys for external services (Allen Brain Atlas, etc.)

### Testing Considerations
- Mock HPC systems for testing job submission
- Test data for parameter metadata queries
- Integration tests for script generation

---

## Next Steps

1. **Review and prioritize** this roadmap with the team
2. **Create GitHub issues** for each high-priority task
3. **Set up development branches** for major features
4. **Begin with architecture documentation** - helps guide all other development
5. **Implement parameter metadata service** - high value, manageable scope
6. **Add SnakeMake generation** - enables HPC workflows

---

## Questions for Clarification

1. **Parameter Metadata Sources**: Which specific databases should be integrated first?
2. **HPC Access**: What HPC systems need to be supported initially? (Fugaku, local cluster, cloud?)
3. **GraphQL Scope**: What specific queries should the GraphQL interface support?
4. **Resource Discovery**: What level of resource discovery is feasible? (Full auto-detection vs. user configuration)
5. **Job Manager Priority**: Which job managers should be implemented first? (SLURM seems most common)

---

*Generated from meeting transcription analysis - November 2025*



