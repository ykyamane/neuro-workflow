# Parameter Metadata API Implementation

## ✅ Completed

We've successfully implemented the Parameter Metadata API endpoint!

### What Was Created

1. **New Django App**: `app/metadata/`
   - `apps.py` - App configuration
   - `views.py` - API views with two endpoints
   - `serializers.py` - Request/response serializers
   - `urls.py` - URL routing

2. **API Endpoints**:
   - `GET /api/metadata/parameters/suggest/` - Get parameter value suggestions
   - `GET /api/metadata/parameters/species-specific/` - Get species-specific parameters

3. **Integration**:
   - Added to main URL configuration (`config/urls.py`)
   - Registered in Django settings (`config/settings.py`)
   - Integrated with existing `ParameterMetadataService` (stub implementation)

---

## 📋 API Documentation

### Endpoint 1: Parameter Suggestions

**URL**: `GET /api/metadata/parameters/suggest/`

**Query Parameters**:
- `parameter_name` (required): Name of the parameter
- `parameter_description` (required): Description of the parameter
- `node_type` (optional): Type of node this parameter belongs to
- `species` (optional): Species to query for (mouse, monkey, human, etc.)
- `context` (optional): Additional context as JSON string

**Example Request**:
```
GET /api/metadata/parameters/suggest/?parameter_name=firing_rate&parameter_description=Average+firing+rate+in+Hz&species=mouse
```

**Example Response**:
```json
{
  "suggestions": [
    {
      "value": 5.0,
      "source": "allen_brain",
      "confidence": 0.7,
      "description": "Typical firing rate for cortical neurons",
      "species": "mouse",
      "citation": "Allen Brain Atlas - Cell Types Database",
      "metadata": {}
    }
  ],
  "parameter_name": "firing_rate",
  "parameter_description": "Average firing rate in Hz",
  "species": "mouse"
}
```

---

### Endpoint 2: Species-Specific Parameters

**URL**: `GET /api/metadata/parameters/species-specific/`

**Query Parameters**:
- `node_type` (required): Type of node
- `species` (required): Species (mouse, monkey, human, etc.)
- `parameter_names` (optional): Comma-separated list of specific parameters to query

**Example Request**:
```
GET /api/metadata/parameters/species-specific/?node_type=SNNbuilder_SingleNeuron&species=mouse&parameter_names=firing_rate,membrane_capacitance
```

**Example Response**:
```json
{
  "node_type": "SNNbuilder_SingleNeuron",
  "species": "mouse",
  "parameters": {
    "firing_rate": 5.0,
    "membrane_capacitance": 100.0
  }
}
```

---

## 🔧 How It Works

1. **Import Handling**: The view tries multiple import paths to find `ParameterMetadataService`:
   - First tries direct import (if neuroworkflow is installed)
   - Then tries adding `../../../../src` to Python path
   - Falls back gracefully if service is unavailable

2. **Service Integration**: Uses the existing stub `ParameterMetadataService`:
   - Currently returns example values based on keyword matching
   - When API credentials arrive, can be swapped for real service
   - No code changes needed in the API layer!

3. **Error Handling**: 
   - Validates request parameters
   - Handles service unavailability gracefully
   - Returns proper HTTP status codes
   - Logs errors for debugging

---

## 🧪 Testing

### Test with curl:

```bash
# Test parameter suggestions
curl "http://localhost:3000/api/metadata/parameters/suggest/?parameter_name=firing_rate&parameter_description=Average+firing+rate+in+Hz&species=mouse"

# Test species-specific parameters
curl "http://localhost:3000/api/metadata/parameters/species-specific/?node_type=SNNbuilder_SingleNeuron&species=mouse"
```

### Test in browser:

1. Start the backend:
   ```bash
   cd gui
   docker-compose up backend
   ```

2. Open in browser:
   ```
   http://localhost:3000/api/metadata/parameters/suggest/?parameter_name=firing_rate&parameter_description=Average+firing+rate+in+Hz&species=mouse
   ```

---

## 🚀 Next Steps

1. **Test the API**: Verify it works with the stub service
2. **Frontend Integration**: Build the UI component to call this API
3. **Real Database Connection**: When API credentials arrive, update `ParameterMetadataService` to use real databases

---

## 📝 Notes

- The API currently uses the **stub implementation** of `ParameterMetadataService`
- This means it returns example values, not real database queries
- When API credentials arrive, we only need to update the service implementation
- The API endpoints will work automatically with real data!

---

*Implementation completed: December 2025*

