# Custom Database Integration Feature

## Overview
This feature allows users to add their own custom database sources for parameter suggestions, similar to the built-in databases (Allen Brain Atlas, NeuroMorpho, PubMed, NeuroML-DB).

## Architecture

### Backend Components

#### 1. Database Model (`app/metadata/models.py`)
- **CustomDatabase**: Django model for storing user-configured database sources
  - Fields: name, description, base_url, api_key, config (JSON), adapter_type, is_active, is_verified, etc.
  - Methods: `get_config_dict()`, `to_adapter_config()`

#### 2. Generic Database Adapter (`src/neuroworkflow/utils/database_adapters/generic.py`)
- **GenericDatabaseAdapter**: Flexible adapter that can be configured for different API patterns
  - Supports REST API pattern (GET/POST requests)
  - Configurable authentication (API key, Bearer token, Basic auth)
  - Extracts parameter values from various response formats
  - Calculates statistics (mean, median, min, max) from retrieved values

#### 3. Connection Tester (`src/neuroworkflow/utils/database_adapters/connection_tester.py`)
- **DatabaseConnectionTester**: Tests connections and determines working adapter patterns
  - Tries multiple adapter patterns automatically
  - Tests different endpoints (/query, /search, /api/query, etc.)
  - Tests different authentication methods
  - Provides helpful error messages and suggestions if connection fails

#### 4. API Endpoints (`app/metadata/views.py`)
- **CustomDatabaseListView**: 
  - `GET /api/metadata/custom-databases/` - List all custom databases
  - `POST /api/metadata/custom-databases/` - Create a new custom database (with automatic connection testing)
- **CustomDatabaseDetailView**:
  - `GET /api/metadata/custom-databases/{id}/` - Get database details
  - `PUT /api/metadata/custom-databases/{id}/` - Update database (re-tests connection if URL/key changed)
  - `DELETE /api/metadata/custom-databases/{id}/` - Delete database (soft delete)
- **DatabaseConnectionTestView**:
  - `POST /api/metadata/custom-databases/test-connection/` - Test connection before creating

#### 5. Integration with ParameterMetadataService
- Updated `ParameterMetadataService` to load custom databases from Django database
- Added `_load_custom_databases()` method
- Added `add_custom_database()` method for dynamic addition
- Custom databases are automatically included in parameter suggestion queries

### Frontend Components (To Be Implemented)

#### 1. CustomDatabaseModal Component
- Form for adding/editing custom databases
- Fields: name, description, base_url, api_key, config (JSON editor)
- "Test Connection" button that calls the test endpoint
- Shows connection test results and suggestions

#### 2. CustomDatabaseList Component
- List of all custom databases
- Shows status (verified/not verified)
- Edit/Delete buttons
- Add new database button

## How It Works

### Adding a Custom Database

1. **User provides credentials**:
   - Base URL (e.g., `https://api.example.com`)
   - API key (if required)
   - Optional: Additional configuration (headers, query params, etc.)

2. **System tests connection**:
   - Tries multiple adapter patterns automatically
   - Tests different endpoints and authentication methods
   - Determines which pattern works

3. **If successful**:
   - Database is saved to Django database
   - Adapter is created and added to ParameterMetadataService
   - Database is marked as `is_verified=True`
   - Working adapter pattern is saved in config

4. **If unsuccessful**:
   - Error message is shown
   - Suggestions are provided (check URL, API key, network, etc.)
   - Database is saved but marked as `is_verified=False`

### Using Custom Databases

Once added and verified, custom databases are automatically included in parameter suggestion queries:
- When a user requests parameter suggestions, the system queries:
  1. Built-in databases (Allen Brain, NeuroMorpho, PubMed, NeuroML-DB)
  2. Custom databases (all active and verified)
  3. OpenAI LLM (if available)

- Results from custom databases are included in the suggestions with:
  - Source name (user-provided database name)
  - Confidence score (0.6 for generic adapter, can be adjusted)
  - Statistics (mean, median, min, max, count)
  - Metadata (source URL, etc.)

## Database Migration

To use this feature, you need to run Django migrations:

```bash
cd gui/workflow_backend/django-project
python manage.py makemigrations metadata
python manage.py migrate
```

## API Usage Examples

### Test Connection
```bash
POST /api/metadata/custom-databases/test-connection/
{
  "base_url": "https://api.example.com",
  "api_key": "your-api-key",
  "config": {}
}
```

### Create Custom Database
```bash
POST /api/metadata/custom-databases/
{
  "name": "My Custom Database",
  "description": "A neuroscience parameter database",
  "base_url": "https://api.example.com",
  "api_key": "your-api-key",
  "adapter_type": "rest_api",
  "is_active": true
}
```

### List Custom Databases
```bash
GET /api/metadata/custom-databases/
```

### Update Custom Database
```bash
PUT /api/metadata/custom-databases/{id}/
{
  "name": "Updated Name",
  "api_key": "new-api-key"
}
```

## Future Enhancements

1. **GraphQL Support**: Implement GraphQL adapter pattern
2. **SDK Support**: Support for Python SDK-based databases
3. **Advanced Configuration**: More flexible query parameter templates
4. **Response Format Detection**: Automatically detect response format
5. **Caching**: Cache query results for better performance
6. **Rate Limiting**: Respect API rate limits
7. **Frontend UI**: Complete React components for managing databases

## Files Created/Modified

### New Files
- `gui/workflow_backend/django-project/app/metadata/models.py`
- `src/neuroworkflow/utils/database_adapters/generic.py`
- `src/neuroworkflow/utils/database_adapters/connection_tester.py`
- `logs/CUSTOM_DATABASE_FEATURE.md` (this file)

### Modified Files
- `gui/workflow_backend/django-project/app/metadata/serializers.py`
- `gui/workflow_backend/django-project/app/metadata/views.py`
- `gui/workflow_backend/django-project/app/metadata/urls.py`
- `src/neuroworkflow/utils/parameter_metadata_service.py`
- `src/neuroworkflow/utils/database_adapters/__init__.py`

## Testing

To test the feature:

1. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

2. **Test connection endpoint**:
   ```bash
   curl -X POST http://localhost:8000/api/metadata/custom-databases/test-connection/ \
     -H "Content-Type: application/json" \
     -d '{"base_url": "https://api.example.com", "api_key": "test-key"}'
   ```

3. **Create a custom database**:
   ```bash
   curl -X POST http://localhost:8000/api/metadata/custom-databases/ \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test DB",
       "base_url": "https://api.example.com",
       "api_key": "test-key"
     }'
   ```

4. **Query parameter suggestions** (should include custom database):
   ```bash
   curl "http://localhost:8000/api/metadata/parameters/suggest/?parameter_name=firing_rate&parameter_description=Neuronal+firing+rate"
   ```
