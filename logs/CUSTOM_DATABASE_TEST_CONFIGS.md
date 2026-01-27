# Custom Database Test Configurations

This document provides test configurations for the custom database feature, including:
1. A real public neuroscience database with REST API
2. Configuration for one of our existing databases (NeuroMorpho) to test integration

## Test Database 1: NeuroMorpho.org (Our Existing Database)

**Purpose**: Test if the generic adapter can work with one of our existing databases

### Configuration:
```json
{
  "name": "NeuroMorpho (Test via Generic Adapter)",
  "description": "Testing generic adapter with NeuroMorpho API",
  "base_url": "https://neuromorpho.org/api",
  "api_key": "",
  "adapter_type": "rest_api",
  "is_active": true,
  "config": {
    "query_endpoint": "/neuron/select",
    "auth_type": "none",
    "query_params_template": {
      "q": "species:mouse"
    }
  }
}
```

### Manual Test:
```bash
# Test the connection
curl -X POST http://localhost:3000/api/metadata/custom-databases/test-connection/ \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://neuromorpho.org/api",
    "api_key": "",
    "config": {
      "query_endpoint": "/neuron/select",
      "auth_type": "none"
    }
  }'

# Create the database
curl -X POST http://localhost:3000/api/metadata/custom-databases/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NeuroMorpho (Test)",
    "description": "Testing generic adapter with NeuroMorpho",
    "base_url": "https://neuromorpho.org/api",
    "api_key": "",
    "adapter_type": "rest_api",
    "is_active": true,
    "config": {
      "query_endpoint": "/neuron/select",
      "auth_type": "none"
    }
  }'
```

### Expected Behavior:
- Connection test should succeed (server is reachable)
- The generic adapter may not extract values perfectly (since NeuroMorpho requires specific query patterns)
- This tests that the generic adapter can at least connect to a real API

---

## Test Database 2: OpenNeuro (Public Neuroimaging Data)

**Purpose**: Test with a real public neuroscience database that has a REST API

### About OpenNeuro:
- **URL**: https://openneuro.org
- **API**: https://api.openneuro.org
- **Description**: Public repository for neuroimaging data (fMRI, EEG, etc.)
- **API Key**: Not required for basic queries
- **Documentation**: https://github.com/OpenNeuroOrg/openneuro/blob/master/docs/api.md

### Configuration:
```json
{
  "name": "OpenNeuro",
  "description": "Public repository for neuroimaging datasets",
  "base_url": "https://api.openneuro.org",
  "api_key": "",
  "adapter_type": "rest_api",
  "is_active": true,
  "config": {
    "query_endpoint": "/datasets",
    "auth_type": "none",
    "query_params_template": {}
  }
}
```

### Manual Test:
```bash
# Test the connection
curl -X POST http://localhost:3000/api/metadata/custom-databases/test-connection/ \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://api.openneuro.org",
    "api_key": "",
    "config": {
      "query_endpoint": "/datasets",
      "auth_type": "none"
    }
  }'

# Create the database
curl -X POST http://localhost:3000/api/metadata/custom-databases/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenNeuro",
    "description": "Public repository for neuroimaging datasets",
    "base_url": "https://api.openneuro.org",
    "api_key": "",
    "adapter_type": "rest_api",
    "is_active": true,
    "config": {
      "query_endpoint": "/datasets",
      "auth_type": "none"
    }
  }'
```

### Expected Behavior:
- Connection test should succeed
- API returns dataset information (may not have direct parameter values, but tests connectivity)

---

## Test Database 3: NeuroElectro (Electrophysiology Database)

**Purpose**: Test with a neuroscience database focused on electrophysiology parameters

### About NeuroElectro:
- **URL**: http://neuroelectro.org
- **API**: REST API available (check documentation)
- **Description**: Database of neuronal electrophysiological properties
- **Focus**: Firing rates, membrane properties, channel properties

### Configuration (if API is available):
```json
{
  "name": "NeuroElectro",
  "description": "Database of neuronal electrophysiological properties",
  "base_url": "http://neuroelectro.org/api",
  "api_key": "",
  "adapter_type": "rest_api",
  "is_active": true,
  "config": {
    "query_endpoint": "/neuron",
    "auth_type": "none"
  }
}
```

**Note**: Verify the actual API endpoint before using this.

---

## Test Database 4: Cell Types Database (Allen Institute)

**Purpose**: Test with Allen Institute's Cell Types Database (different from Allen Brain Atlas)

### About:
- **URL**: https://celltypes.brain-map.org
- **API**: Uses Allen SDK, but may have REST endpoints
- **Description**: Database of cell types with electrophysiology data

### Configuration (if REST API available):
```json
{
  "name": "Allen Cell Types",
  "description": "Allen Institute Cell Types Database",
  "base_url": "https://api.brain-map.org/api/v2",
  "api_key": "",
  "adapter_type": "rest_api",
  "is_active": true,
  "config": {
    "query_endpoint": "/data/query",
    "auth_type": "none"
  }
}
```

---

## Quick Test Commands

### 1. Test NeuroMorpho Connection:
```bash
curl -X POST http://localhost:3000/api/metadata/custom-databases/test-connection/ \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://neuromorpho.org/api",
    "api_key": ""
  }'
```

### 2. Test OpenNeuro Connection:
```bash
curl -X POST http://localhost:3000/api/metadata/custom-databases/test-connection/ \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://api.openneuro.org",
    "api_key": ""
  }'
```

### 3. Create NeuroMorpho Test Database:
```bash
curl -X POST http://localhost:3000/api/metadata/custom-databases/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NeuroMorpho Test",
    "description": "Testing with NeuroMorpho API",
    "base_url": "https://neuromorpho.org/api",
    "adapter_type": "rest_api",
    "is_active": true
  }'
```

### 4. Query Parameter Suggestions (should include custom databases):
```bash
curl "http://localhost:3000/api/metadata/parameters/suggest/?parameter_name=dendrite_length&parameter_description=Total+length+of+dendrites&species=mouse"
```

---

## Expected Results

### Connection Test:
- ✅ **NeuroMorpho**: Should succeed (server is reachable)
- ✅ **OpenNeuro**: Should succeed (public API)
- ❌ **Fake URL**: Should fail with helpful error message

### Parameter Queries:
- Custom databases should appear in the suggestions list
- Source name should be the database name you provided
- Confidence may be lower (0.6) for generic adapter
- Values should be extracted if the API response format matches expected patterns

---

## Notes

1. **Generic Adapter Limitations**: 
   - The generic adapter tries common response patterns but may not work perfectly with all APIs
   - It's designed to work with REST APIs that return data in common formats (JSON arrays/objects)
   - For best results, the API should return parameter values in a predictable format

2. **Response Format Expectations**:
   - The generic adapter looks for values in:
     - Arrays of objects with `value`, `data`, or `parameter_value` fields
     - Objects with `results`, `data`, or `items` arrays
     - Direct `value` fields in the response

3. **Testing Strategy**:
   - Start with connection tests (verify connectivity)
   - Then test with real parameter queries
   - Check if values are extracted correctly
   - Verify they appear in parameter suggestions
