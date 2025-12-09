# Work We Can Do While Waiting for API Credentials

**Status**: Waiting for API credentials (Allen Brain Atlas, NeuroMorpho.org)  
**Goal**: Build infrastructure and UI components that will work with real APIs when credentials arrive

---

## 🎯 Priority 1: Backend API Endpoints (Can Use Stub Service)

### 1.1 Parameter Metadata API Endpoint

**What**: Create REST API endpoint for parameter suggestions  
**Why**: Frontend needs this to display suggestions, can use stub service now  
**Location**: `gui/workflow_backend/django-project/app/metadata/` (new app)

**Tasks**:
- [ ] Create new Django app: `app/metadata/`
- [ ] Create view: `ParameterSuggestionView` 
- [ ] Add endpoint: `GET /api/metadata/parameters/suggest/`
- [ ] Integrate with existing `ParameterMetadataService` (stub)
- [ ] Add URL routing
- [ ] Add request/response serializers
- [ ] Add error handling

**Endpoint Design**:
```python
GET /api/metadata/parameters/suggest/
Query Parameters:
  - parameter_name: str
  - parameter_description: str
  - species: str (optional)
  - node_type: str (optional)

Response:
{
  "suggestions": [
    {
      "value": 5.0,
      "source": "allen_brain",
      "confidence": 0.7,
      "metadata": {...}
    }
  ]
}
```

**Estimated Time**: 2-3 days

---

### 1.2 Job Management API Endpoints

**What**: Create REST API endpoints for HPC job submission  
**Why**: Enables job submission from frontend, doesn't need real HPC access for structure  
**Location**: `gui/workflow_backend/django-project/app/workflow/views.py` (extend)

**Tasks**:
- [ ] Add endpoint: `POST /api/workflow/{workflow_id}/generate-job-script/`
- [ ] Add endpoint: `POST /api/workflow/{workflow_id}/submit-job/`
- [ ] Add endpoint: `GET /api/workflow/{workflow_id}/job-status/{job_id}/`
- [ ] Add endpoint: `GET /api/workflow/{workflow_id}/available-resources/`
- [ ] Integrate with `SLURMJobManager`
- [ ] Add request/response serializers
- [ ] Add error handling

**Endpoint Designs**:
```python
POST /api/workflow/{workflow_id}/generate-job-script/
Body: {
  "job_manager_type": "slurm",
  "resource_requirements": {
    "cpus": 8,
    "memory_gb": 16.0,
    "walltime_hours": 2.0
  }
}

POST /api/workflow/{workflow_id}/submit-job/
Body: {
  "job_script_path": "/path/to/script.sh",
  "job_manager_type": "slurm"
}

GET /api/workflow/{workflow_id}/job-status/{job_id}/
Response: {
  "job_id": "12345",
  "status": "running",
  "submitted_at": "2025-12-03T10:00:00Z"
}
```

**Estimated Time**: 3-4 days

---

## 🎯 Priority 2: Frontend UI Components

### 2.1 Parameter Suggestion UI Component

**What**: React component to display and accept parameter suggestions  
**Why**: Users need UI to see suggestions, can use mock data now  
**Location**: `gui/workflow_frontend/src/views/home/components/ParameterSuggestionModal.tsx` (new)

**Tasks**:
- [ ] Create `ParameterSuggestionModal.tsx` component
- [ ] Add "Suggest Values" button to node detail modal
- [ ] Display suggestions with source and confidence
- [ ] Allow accept/reject functionality
- [ ] Show loading states
- [ ] Add error handling
- [ ] Style with Chakra UI (match existing design)

**Component Design**:
```tsx
<ParameterSuggestionModal
  isOpen={isOpen}
  onClose={onClose}
  parameterName="firing_rate"
  parameterDescription="Average firing rate in Hz"
  species="mouse"
  onAccept={(suggestion) => {...}}
/>
```

**Integration Point**: Add to `nodeDetailModal.tsx`

**Estimated Time**: 3-4 days

---

### 2.2 Job Management UI Component

**What**: React component for HPC job submission and monitoring  
**Why**: Users need UI to submit jobs, can test with mock responses  
**Location**: `gui/workflow_frontend/src/views/home/components/JobSubmissionModal.tsx` (new)

**Tasks**:
- [ ] Create `JobSubmissionModal.tsx` component
- [ ] Add job manager type selector (SLURM, PBS, etc.)
- [ ] Add resource requirements form (CPUs, memory, GPU, walltime)
- [ ] Add job submission button
- [ ] Add job status display
- [ ] Add job logs viewer
- [ ] Style with Chakra UI

**Component Design**:
```tsx
<JobSubmissionModal
  isOpen={isOpen}
  onClose={onClose}
  workflowId={workflowId}
  onJobSubmitted={(jobId) => {...}}
/>
```

**Integration Point**: Add to workflow toolbar or node detail modal

**Estimated Time**: 4-5 days

---

## 🎯 Priority 3: Additional Job Managers

### 3.1 PBS/Torque Job Manager

**What**: Implement PBS job manager (similar to SLURM)  
**Why**: Many HPC systems use PBS, no API credentials needed  
**Location**: `src/neuroworkflow/utils/job_managers/pbs.py` (new)

**Tasks**:
- [ ] Create `PBSJobManager` class
- [ ] Implement `generate_job_script()` method
- [ ] Implement `submit_job()` method
- [ ] Implement `get_job_status()` method
- [ ] Implement `cancel_job()` method
- [ ] Add tests

**Estimated Time**: 2-3 days

---

### 3.2 AWS Batch Job Manager

**What**: Implement AWS Batch job manager  
**Why**: Cloud HPC option, can use AWS SDK (credentials needed later)  
**Location**: `src/neuroworkflow/utils/job_managers/aws_batch.py` (new)

**Tasks**:
- [ ] Create `AWSBatchJobManager` class
- [ ] Implement job script generation
- [ ] Implement job submission (stub for now)
- [ ] Add AWS SDK dependency
- [ ] Add configuration for AWS credentials

**Note**: Can build structure now, will need AWS credentials later

**Estimated Time**: 3-4 days

---

## 🎯 Priority 4: Documentation

### 4.1 API Documentation

**What**: Complete REST API reference documentation  
**Why**: Helps developers and users, no dependencies  
**Location**: `docs/API.md` (new)

**Tasks**:
- [ ] Document all existing endpoints
- [ ] Document new metadata endpoints
- [ ] Document new job management endpoints
- [ ] Add request/response examples
- [ ] Add authentication info
- [ ] Add error codes

**Estimated Time**: 2-3 days

---

### 4.2 Development Guide

**What**: Setup and development instructions  
**Why**: Helps new developers, no dependencies  
**Location**: `docs/DEVELOPMENT.md` (new)

**Tasks**:
- [ ] Development environment setup
- [ ] Code structure and conventions
- [ ] Testing guidelines
- [ ] Contribution workflow
- [ ] Deployment process

**Estimated Time**: 2-3 days

---

## 🎯 Priority 5: Node Code Generation

### 5.1 Implement `python_code()` Methods in Nodes

**What**: Make nodes generate standalone Python code  
**Why**: Enables full SnakeMake workflow execution, no dependencies  
**Location**: `gui/workflow_backend/django-project/codes/nodes/` (modify existing nodes)

**Tasks**:
- [ ] Add `python_code()` method to base `Node` class
- [ ] Implement `python_code()` for core nodes:
  - [ ] `BuildSonataNetworkNode`
  - [ ] `SonataNetworkSimulationNode`
  - [ ] `NESTNeuronSetupNode`
  - [ ] Other simulation nodes
- [ ] Update SnakeMake generator to use `python_code()`
- [ ] Test generated code

**Estimated Time**: 1-2 weeks

---

## 📋 Recommended Implementation Order

### Week 1: Backend APIs
1. **Day 1-2**: Parameter Metadata API endpoint
2. **Day 3-4**: Job Management API endpoints
3. **Day 5**: Testing and documentation

### Week 2: Frontend UI
1. **Day 1-3**: Parameter Suggestion UI component
2. **Day 4-5**: Job Management UI component

### Week 3: Additional Features
1. **Day 1-2**: PBS Job Manager
2. **Day 3-4**: AWS Batch Job Manager (structure)
3. **Day 5**: Documentation

### Week 4: Node Code Generation
1. **Day 1-5**: Implement `python_code()` methods

---

## ✅ What We'll Have When API Credentials Arrive

1. **Complete Backend Infrastructure**
   - REST API endpoints ready
   - Stub service can be swapped for real service
   - Error handling in place

2. **Complete Frontend UI**
   - Components ready to display real data
   - Just need to connect to real API endpoints
   - User experience already tested

3. **Multiple Job Managers**
   - SLURM (done)
   - PBS (done)
   - AWS Batch (structure done)

4. **Better Documentation**
   - API reference complete
   - Development guide available

5. **Enhanced SnakeMake Generation**
   - Nodes can generate actual code
   - Workflows are fully executable

---

## 🚀 Quick Wins (Can Start Today)

1. **Parameter Metadata API Endpoint** (2-3 days)
   - High value
   - No dependencies
   - Frontend can start using it immediately

2. **Parameter Suggestion UI Component** (3-4 days)
   - High visibility
   - Users can see it working (with stub data)
   - Easy to test

3. **API Documentation** (2-3 days)
   - Low effort
   - High value for developers
   - No dependencies

---

## 📝 Notes

- **Stub Service**: The parameter metadata service stub will work perfectly for testing UI and API structure
- **Mock Data**: Frontend can use mock data to develop and test components
- **Job Managers**: Can build structure and test script generation without actual HPC access
- **Documentation**: Can be written based on current code structure

---

## 🎯 Recommendation

**Start with Priority 1.1 (Parameter Metadata API)** because:
- ✅ Quick to implement (2-3 days)
- ✅ High value (enables frontend work)
- ✅ No dependencies
- ✅ Can test immediately with stub service
- ✅ Easy to swap stub for real service later

Then move to Priority 2.1 (Parameter Suggestion UI) to have a complete feature working end-to-end (even with stub data).

---

*This plan ensures we make progress while waiting for API credentials, and everything will work seamlessly when credentials arrive!*

