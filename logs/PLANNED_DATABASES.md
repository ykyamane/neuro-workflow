# Planned Database Integrations

## 📋 Original Plan (from IMPROVEMENT_PLAN.md)

The improvement plan listed **4 databases** to integrate:

### 1. ✅ **Allen Brain Atlas** - **IMPLEMENTED**
- **Status**: ✅ Fully implemented and working
- **Type**: Electrophysiology data
- **API**: `allensdk` Python library
- **API Key Required**: ❌ No (free/public API)
- **Parameters**: 56 electrophysiology fields
- **Coverage**: Firing rates, membrane properties, spike properties, voltage/current measurements

### 2. ✅ **NeuroMorpho.org** - **IMPLEMENTED**
- **Status**: ✅ Fully implemented and working
- **Type**: Morphological data
- **API**: REST API
- **API Key Required**: ❌ No (free/public API)
- **Parameters**: 16 morphological fields
- **Coverage**: Size measurements, branching properties, distance measurements, complexity metrics

### 3. ⏳ **PubMed/NCBI** - **NOT YET IMPLEMENTED**
- **Status**: ⏳ Planned but not implemented
- **Type**: Research papers and literature
- **API**: NCBI E-utilities API or PubMed API
- **API Key Required**: ⚠️ Possibly (depends on usage volume)
- **Purpose**: Find parameter values from published research papers
- **Use Case**: Search for parameter values mentioned in papers, extract citations

**Why Not Implemented Yet**:
- Lower priority (Allen Brain Atlas and NeuroMorpho provide structured data)
- More complex (need to parse papers, extract values)
- May require API keys for high-volume usage
- Can be added later if needed

**How It Would Work**:
- Search PubMed for papers mentioning the parameter
- Extract parameter values from abstracts/full text
- Provide citations from actual papers
- More current than static databases

### 4. ⏳ **NeuroML Database** - **NOT YET IMPLEMENTED**
- **Status**: ⏳ Planned but not implemented
- **Type**: Model parameters from NeuroML models
- **API**: Unknown (may need to check if API exists)
- **API Key Required**: ❓ Unknown
- **Purpose**: Get parameter values from validated NeuroML models
- **Use Case**: Find parameters used in published NeuroML models

**Why Not Implemented Yet**:
- Lower priority
- May not have a public API
- Would need to investigate availability
- Can be added later if needed

**How It Would Work**:
- Query NeuroML database for models with similar parameters
- Extract parameter values from model definitions
- Provide model citations

---

## 🎯 Current Implementation Status

### Implemented (2/4):
- ✅ Allen Brain Atlas
- ✅ NeuroMorpho.org

### Planned but Not Implemented (2/4):
- ⏳ PubMed/NCBI
- ⏳ NeuroML Database

---

## 💡 Why These Two Were Prioritized

1. **No API Keys Required**: Both Allen Brain Atlas and NeuroMorpho are free/public APIs
2. **Structured Data**: Both provide well-structured, queryable data
3. **High Value**: Cover the most common parameter types (electrophysiology + morphology)
4. **Easy Integration**: Both have good Python libraries/APIs

---

## 🚀 Future Additions

### PubMed/NCBI Integration

**Benefits**:
- Access to current research
- Parameter values from recent papers
- Real citations from publications
- Can find values not in structured databases

**Challenges**:
- Need to parse unstructured text
- Extract values from papers
- Handle different paper formats
- May need API keys for high volume

**Implementation Approach**:
1. Use NCBI E-utilities API to search PubMed
2. Use AI to extract parameter values from abstracts/full text
3. Provide paper citations
4. Could use OpenAI to parse and extract values

### NeuroML Database Integration

**Benefits**:
- Validated model parameters
- Parameters from published models
- Model citations
- Standardized format (NeuroML)

**Challenges**:
- Need to check if public API exists
- May need to parse NeuroML files directly
- Database may not be publicly accessible

**Implementation Approach**:
1. Check if NeuroML database has public API
2. If yes, create adapter similar to Allen Brain/NeuroMorpho
3. If no, could parse NeuroML files from repositories
4. Extract parameters from model definitions

---

## 📊 Current System Coverage

With the 2 implemented databases, we cover:

- **Electrophysiology**: ✅ Allen Brain Atlas (56 parameters)
- **Morphology**: ✅ NeuroMorpho (16 parameters)
- **Total**: 72 structured parameters

**Gaps**:
- Recent research findings (would need PubMed)
- Model-specific parameters (would need NeuroML)
- Parameters not in structured databases (currently handled by AI generation)

---

## 🎯 Recommendation

**Current Status**: The 2 implemented databases provide excellent coverage for the most common neuroscience parameters.

**Future Additions**:
- **PubMed/NCBI**: Would be valuable for current research and parameters not in structured databases
- **NeuroML Database**: Would be valuable if there's a public API and if users need model-specific parameters

**Priority**: 
1. ✅ **Done**: Allen Brain Atlas, NeuroMorpho
2. **Medium Priority**: PubMed/NCBI (if users need current research)
3. **Low Priority**: NeuroML Database (if API exists and users need it)

---

## 🔧 Adding New Databases

The system is designed to easily add new databases:

1. Create new adapter class inheriting from `DatabaseAdapter`
2. Implement `query_parameter()` method
3. Implement `get_source_name()` method
4. Add to `MetadataSource` enum
5. Register in `ParameterMetadataService._initialize_database_adapters()`

**Example Structure**:
```python
class PubMedAdapter(DatabaseAdapter):
    def query_parameter(self, parameter_name, parameter_description, species, context):
        # Search PubMed
        # Extract values from papers
        # Return suggestions
        pass
```

---

*Last Updated: December 2025*

