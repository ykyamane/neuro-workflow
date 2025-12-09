# Immediate Action Items from Meeting Analysis

This document summarizes the most actionable codebase improvements identified from the meeting transcription.

## Quick Wins (Can Start Immediately)

### 1. Extend Script Exporter for SnakeMake
**Current State**: Only Python scripts are generated  
**Action**: Add SnakeMake script generation capability

**Files to Modify**:
- `src/neuroworkflow/utils/script_exporter.py` - Add SnakeMake export option
- `src/neuroworkflow/core/schema.py` - Already has I/O port types (FILE_PATH, HDF5_FILE, etc.) which are perfect for SnakeMake

**Why This is Easy**:
- The codebase already defines I/O port types in `PortType` enum
- SnakeMake workflows map naturally to file-based node outputs
- Can reuse existing script generation logic

**Estimated Effort**: 2-3 days

---

### 2. Add Parameter Metadata Fields to Schema
**Current State**: Parameters have `name` and `description` only  
**Action**: Extend `ParameterDefinition` to support metadata sources

**Files to Modify**:
- `src/neuroworkflow/core/schema.py` - Extend `ParameterDefinition` dataclass

**Changes Needed**:
```python
@dataclass
class ParameterDefinition:
    default_value: Any = None
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    optimizable: bool = False
    optimization_range: Optional[List[Any]] = None
    # NEW FIELDS:
    metadata_sources: List[str] = field(default_factory=list)  # e.g., ["allen_brain", "neuromorpho"]
    species_specific: bool = False
    suggested_values: List[Dict[str, Any]] = field(default_factory=list)  # Store AI suggestions
```

**Estimated Effort**: 1-2 hours

---

### 3. Create Architecture Documentation Structure
**Current State**: Scattered documentation files  
**Action**: Create comprehensive architecture documentation

**Files to Create**:
- `docs/ARCHITECTURE.md` - System architecture overview
- `docs/API.md` - Complete API reference
- `docs/DEVELOPMENT.md` - Development guide

**Why This is Important**:
- Meeting explicitly requested this
- Helps with onboarding (you mentioned needing to understand the system)
- Guides all future development

**Estimated Effort**: 3-5 days (can be done incrementally)

---

## Medium-Term Projects (1-2 Weeks)

### 4. Parameter Metadata Service (Basic Version)
**Action**: Create service interface for querying parameter metadata

**Files to Create**:
- `src/neuroworkflow/utils/parameter_metadata_service.py`
- `gui/workflow_backend/django-project/app/metadata/` (new app)
  - `views.py` - API endpoints
  - `urls.py` - URL routing

**Initial Implementation**:
- Mock/stub implementation that returns example data
- Can be extended later with real database connections
- Provides API structure for frontend integration

**Estimated Effort**: 1 week

---

### 5. Job Manager Abstraction Layer
**Action**: Create base classes for HPC job submission

**Files to Create**:
- `src/neuroworkflow/utils/job_managers/base.py` - Abstract base class
- `src/neuroworkflow/utils/job_managers/slurm.py` - SLURM implementation (most common)

**Initial Implementation**:
- Start with SLURM only (most widely used)
- Generate job scripts (don't need to submit immediately)
- Can add other job managers incrementally

**Estimated Effort**: 1-2 weeks

---

## Code Locations Reference

### Key Files for Understanding Current System

**Core Schema**:
- `src/neuroworkflow/core/schema.py` - All data structures
- `src/neuroworkflow/core/node.py` - Node base class
- `src/neuroworkflow/core/workflow.py` - Workflow execution

**Script Generation**:
- `src/neuroworkflow/utils/script_exporter.py` - Current script export
- `src/neuroworkflow/nodes/*/SNNbuilder_*.py` - Node script generation methods

**Backend API**:
- `gui/workflow_backend/django-project/app/workflow/views.py` - Workflow API
- `gui/workflow_backend/django-project/app/box/views.py` - Node management API

**Frontend**:
- `gui/workflow_frontend/src/views/home/components/nodeDetailModal.tsx` - Parameter UI
- `gui/workflow_frontend/src/api/` - API client code

---

## Implementation Strategy

### Phase 1: Foundation (Week 1-2)
1. ✅ Create architecture documentation (helps guide everything)
2. ✅ Extend parameter schema with metadata fields
3. ✅ Add SnakeMake script generation

### Phase 2: Metadata Integration (Week 3-4)
1. Create parameter metadata service (stub implementation)
2. Add backend API endpoints
3. Frontend integration for parameter suggestions

### Phase 3: HPC Support (Week 5-6)
1. Create job manager abstraction
2. Implement SLURM job manager
3. Add resource requirements to workflow schema
4. Generate job submission scripts

### Phase 4: Advanced Features (Ongoing)
1. GraphQL interface (contractors working on this)
2. Resource discovery service
3. Additional job managers (AWS, Google Cloud)
4. Format adapters for interoperability

---

## Questions to Resolve Before Starting

1. **SnakeMake Priority**: Should SnakeMake generation be implemented first, or is Python script generation sufficient for now?

2. **Metadata Sources**: Which databases should be integrated first?
   - Allen Brain Atlas
   - NeuroMorpho
   - Custom databases mentioned in meeting

3. **HPC Systems**: Which systems need immediate support?
   - Local cluster (SLURM/Sbatch)
   - Fugaku (mentioned in meeting)
   - Cloud (AWS/Google)

4. **GraphQL**: Since contractors are working on this, should we focus on other areas?

5. **Documentation Format**: What format is preferred?
   - Markdown (current)
   - Sphinx/ReadTheDocs
   - Wiki

---

## Recommended Starting Point

**Start with Architecture Documentation** because:
1. Meeting explicitly requested it
2. You mentioned needing to understand the system deeply
3. It will guide all other development
4. Can be done in parallel with code exploration
5. Helps identify additional improvement opportunities

**Then implement Parameter Metadata Schema Extension** because:
1. Very quick (1-2 hours)
2. Enables future metadata features
3. No breaking changes
4. Can be tested immediately

**Follow with SnakeMake Generation** because:
1. High value (enables HPC workflows)
2. Codebase already has I/O port types defined
3. Natural extension of existing script exporter
4. Can be implemented incrementally

---

*This document should be updated as items are completed and priorities change.*

