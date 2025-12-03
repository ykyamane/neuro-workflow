# Parameter Suggestion Engine - Comprehensive Guide

## 🎯 Overview

The **Parameter Suggestion Engine** is a system that helps users find appropriate parameter values for brain modeling by querying external databases and providing AI-assisted suggestions based on context (species, brain region, neuron type, etc.).

---

## 🧠 The Problem It Solves

### Current Challenge in Brain Modeling

When building brain models, researchers need to set **hundreds of parameters** like:
- Membrane capacitance (C_m)
- Resting membrane potential (V_rest)
- Firing rates
- Synaptic weights
- Time constants
- Conductances
- ... and many more

**The Problem:**
1. ❌ **Hard to find**: Values are scattered across papers, databases, and experiments
2. ❌ **Species-specific**: Mouse neurons ≠ Monkey neurons ≠ Human neurons
3. ❌ **Context-dependent**: Cortical neurons ≠ Hippocampal neurons
4. ❌ **Time-consuming**: Manual literature search takes hours per parameter
5. ❌ **Error-prone**: Easy to use values from wrong species or brain region

### Our Solution

✅ **Automated parameter suggestions** based on:
- Parameter description (acts as a semantic query)
- Species (mouse, monkey, human, etc.)
- Context (brain region, cell type, etc.)
- Multiple trusted data sources

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                           │
│  (GUI or Jupyter Notebook - creates/edits nodes)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              NODE WITH PARAMETERS                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Parameter: "firing_rate"                              │  │
│  │ Description: "Average neuronal firing rate in Hz"     │  │
│  │ Species: "mouse"                                      │  │
│  │ Default: 5.0                                          │  │
│  │                                                       │  │
│  │ [Get Suggestions] ← Button                           │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         PARAMETER METADATA SERVICE                           │
│  (src/neuroworkflow/utils/parameter_metadata_service.py)    │
│                                                              │
│  suggest_parameter_values(                                  │
│      parameter_name="firing_rate",                          │
│      parameter_description="Average firing rate in Hz",     │
│      species="mouse"                                        │
│  )                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL DATA SOURCES                           │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │ Allen Brain   │  │ NeuroMorpho   │  │ Custom DB       │ │
│  │ Atlas         │  │ .org          │  │ (Papers, etc.)  │ │
│  └───────────────┘  └───────────────┘  └─────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 SUGGESTIONS RETURNED                         │
│  [                                                           │
│    {                                                         │
│      value: 5.0,                                            │
│      source: "allen_brain",                                 │
│      confidence: 0.7,                                       │
│      description: "Typical cortical neuron firing rate",   │
│      species: "mouse",                                      │
│      citation: "Allen Brain Atlas - Cell Types DB"         │
│    },                                                        │
│    {                                                         │
│      value: 4.8,                                            │
│      source: "neuromorpho",                                 │
│      confidence: 0.65,                                      │
│      ...                                                     │
│    }                                                         │
│  ]                                                           │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              USER REVIEWS & SELECTS                          │
│  (Human-in-the-loop: accept, reject, or modify)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Core Data Structures

### 1. ParameterSuggestion

Each suggestion is a structured object containing:

```python
@dataclass
class ParameterSuggestion:
    value: Any                      # The suggested parameter value
    source: str                     # Where it came from (e.g., "allen_brain")
    confidence: float               # How confident (0.0 to 1.0)
    description: str                # Human-readable explanation
    species: Optional[str]          # Species this applies to
    citation: Optional[str]         # Academic citation
    metadata: Dict[str, Any]        # Additional context
```

**Example**:
```python
ParameterSuggestion(
    value=10.5,
    source="allen_brain",
    confidence=0.85,
    description="Membrane time constant for Layer 5 pyramidal neurons",
    species="mouse",
    citation="Allen Brain Atlas - Cell Types Database (2023)",
    metadata={
        "brain_region": "visual_cortex",
        "layer": 5,
        "cell_type": "pyramidal",
        "sample_size": 147
    }
)
```

### 2. Extended ParameterDefinition (in Node Schema)

Nodes can now include metadata hints:

```python
@dataclass
class ParameterDefinition:
    default_value: Any = None
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    optimizable: bool = False
    optimization_range: Optional[List[Any]] = None
    
    # NEW METADATA FIELDS:
    metadata_sources: List[str] = field(default_factory=list)
    # ^ Which databases to query: ["allen_brain", "neuromorpho", "custom_db"]
    
    species_specific: bool = False
    # ^ Does this parameter vary by species?
    
    suggested_values: Dict[str, Any] = field(default_factory=dict)
    # ^ Pre-computed suggestions: {"mouse": 10.0, "human": 15.0}
```

---

## 🔍 How It Works

### Step-by-Step Process

#### 1. User Creates/Edits a Node

```python
# User is configuring a neuron model node
build_neuron = CreateNeuronNode("MyNeuron")

# This node has parameters like:
NODE_DEFINITION = {
    "parameters": {
        "tau_m": ParameterDefinition(
            default_value=10.0,
            description="Membrane time constant in milliseconds",
            metadata_sources=["allen_brain", "neuromorpho"],
            species_specific=True,
            constraints={"min": 1.0, "max": 50.0}
        )
    }
}
```

#### 2. System Calls Parameter Metadata Service

```python
from neuroworkflow.utils.parameter_metadata_service import ParameterMetadataService

service = ParameterMetadataService()

suggestions = service.suggest_parameter_values(
    parameter_name="tau_m",
    parameter_description="Membrane time constant in milliseconds",
    species="mouse",
    context={
        "brain_region": "visual_cortex",
        "cell_type": "pyramidal"
    }
)
```

#### 3. Service Queries External Databases

The service:
1. **Parses the description** → identifies this is about membrane time constant
2. **Queries enabled data sources**:
   - Allen Brain Atlas API
   - NeuroMorpho.org database
   - Custom local databases (papers, experiments)
3. **Filters by species** → only mouse data
4. **Filters by context** → visual cortex, pyramidal cells
5. **Ranks results** → by relevance and confidence

#### 4. Returns Structured Suggestions

```python
[
    ParameterSuggestion(
        value=10.5,
        source="allen_brain",
        confidence=0.85,
        description="Layer 5 pyramidal neurons, visual cortex",
        species="mouse",
        citation="Allen Cell Types Database (2023)"
    ),
    ParameterSuggestion(
        value=12.3,
        source="neuromorpho",
        confidence=0.72,
        description="Pyramidal neurons, cortex",
        species="mouse",
        citation="NeuroMorpho.org - Smith et al. (2020)"
    ),
    ParameterSuggestion(
        value=9.8,
        source="custom_db",
        confidence=0.68,
        description="From lab experiments",
        species="mouse",
        citation="Internal data collection"
    )
]
```

#### 5. User Reviews and Selects

The GUI shows:

```
Parameter: tau_m (Membrane time constant)
Current value: 10.0 ms

Suggestions from databases:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 10.5 ms (85% confidence)
  Source: Allen Brain Atlas
  Context: Layer 5 pyramidal neurons, visual cortex
  Citation: Allen Cell Types Database (2023)
  [Use This Value]

◯ 12.3 ms (72% confidence)
  Source: NeuroMorpho.org
  Context: Pyramidal neurons, cortex
  Citation: Smith et al. (2020)
  [Use This Value]

◯ 9.8 ms (68% confidence)
  Source: Custom Database
  Context: Lab experiments
  Citation: Internal data collection
  [Use This Value]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Keep Current] [Enter Custom Value]
```

User clicks **[Use This Value]** on the first suggestion, and the parameter is updated to 10.5 ms.

---

## 🚀 Implementation Status

### ✅ What's Implemented (Current)

1. **Core Service Infrastructure**
   - `ParameterMetadataService` class
   - `ParameterSuggestion` dataclass
   - `MetadataSource` enum
   - Basic query interface

2. **Schema Extensions**
   - `metadata_sources` field in `ParameterDefinition`
   - `species_specific` flag
   - `suggested_values` dictionary

3. **Stub Implementation**
   - Pattern matching on parameter descriptions
   - Example suggestions for common parameters
   - Species filtering

4. **Testing**
   - Comprehensive test in `Test_New_Features.ipynb`
   - 3 test cases (firing rate, membrane capacitance, synaptic weight)
   - Species-specific testing (mouse, human)

### ⏳ What's NOT Implemented (Future Work)

1. **Real Database Connections**
   - Allen Brain Atlas API integration
   - NeuroMorpho.org API integration
   - PubMed literature mining
   - Custom database connectors

2. **Backend API Endpoints**
   - REST API: `GET /api/metadata/parameters/suggest/`
   - Authentication and rate limiting
   - Caching layer

3. **Frontend Integration**
   - "Get Suggestions" button in node parameter editor
   - Suggestion display modal
   - Accept/reject UI
   - Confidence score visualization

4. **Advanced Features**
   - Semantic search using embeddings
   - Machine learning-based ranking
   - Cross-species parameter scaling
   - Literature citation tracking

---

## 🎓 Example Use Cases

### Use Case 1: Setting Firing Rates

**Scenario**: User is building a cortical network model with mouse neurons.

```python
# Node parameter definition
"firing_rate": ParameterDefinition(
    default_value=5.0,
    description="Average baseline firing rate in Hz",
    species_specific=True,
    metadata_sources=["allen_brain"]
)

# User requests suggestions
service = ParameterMetadataService()
suggestions = service.suggest_parameter_values(
    parameter_name="firing_rate",
    parameter_description="Average baseline firing rate in Hz",
    species="mouse",
    context={"brain_region": "visual_cortex", "layer": 4}
)

# System returns:
# [
#   Suggestion: 5.2 Hz (confidence: 0.89)
#     → Layer 4 excitatory neurons in mouse V1
#     → Allen Brain Atlas, n=234 cells
#   Suggestion: 4.8 Hz (confidence: 0.76)
#     → Cortical neurons, visual system
#     → NeuroMorpho.org compilation
# ]
```

**User selects** 5.2 Hz and continues building the model.

### Use Case 2: Cross-Species Comparison

**Scenario**: User wants to test the same model on mouse, monkey, and human.

```python
for species in ["mouse", "monkey", "human"]:
    suggestions = service.suggest_parameter_values(
        parameter_name="C_m",
        parameter_description="Membrane capacitance in pF",
        species=species
    )
    print(f"{species}: {suggestions[0].value} pF")

# Output:
# mouse: 100.0 pF
# monkey: 150.0 pF
# human: 200.0 pF
```

System automatically adjusts parameters based on species.

### Use Case 3: Literature-Driven Parameters

**Scenario**: User wants synaptic parameters from a specific brain region.

```python
suggestions = service.suggest_parameter_values(
    parameter_name="g_syn",
    parameter_description="AMPA synaptic conductance in nS",
    species="rat",
    context={
        "brain_region": "hippocampus",
        "synapse_type": "CA3-CA1",
        "temperature": 32  # °C
    }
)

# Returns suggestions with paper citations:
# [
#   Suggestion: 1.2 nS (confidence: 0.91)
#     → CA3-CA1 excitatory synapses at 32°C
#     → Magee & Cook, J Neurophysiol (2000)
# ]
```

### Use Case 4: AI-Assisted Optimization

**Scenario**: User marks parameters as "optimizable" and wants starting ranges.

```python
"syn_weight": ParameterDefinition(
    default_value=1.0,
    description="Synaptic connection weight",
    optimizable=True,
    optimization_range=None,  # Not set yet
    metadata_sources=["allen_brain", "custom_db"]
)

# System suggests optimization range based on literature:
suggestions = service.suggest_parameter_values(
    parameter_name="syn_weight",
    parameter_description="Synaptic connection weight",
    species="mouse"
)

# System provides range:
# optimization_range = [0.5, 2.0]  # Based on biological data
```

---

## 🔧 Current Implementation (Stub)

### How the Stub Works

Right now, the service uses **simple pattern matching** as a proof-of-concept:

```python
def suggest_parameter_values(self, parameter_name, parameter_description, ...):
    suggestions = []
    
    # Pattern 1: Firing rate
    if "firing rate" in parameter_description.lower():
        suggestions.append(
            ParameterSuggestion(
                value=5.0,  # Hard-coded example
                source="allen_brain",
                confidence=0.7,
                description="Typical firing rate for cortical neurons",
                species=species or "mouse"
            )
        )
    
    # Pattern 2: Membrane potential
    if "membrane potential" in parameter_description.lower():
        suggestions.append(
            ParameterSuggestion(
                value=-65.0,  # Hard-coded example
                source="neuromorpho",
                confidence=0.8,
                description="Typical resting membrane potential"
            )
        )
    
    # ... more patterns ...
    
    return suggestions
```

### Testing the Stub

In the Jupyter notebook:

```python
# Test 1: Firing rate
suggestions = service.suggest_parameter_values(
    parameter_name="firing_rate",
    parameter_description="Average neuronal firing rate in Hz",
    species="mouse"
)

print(suggestions[0].value)  # → 5.0
print(suggestions[0].source)  # → "allen_brain"
print(suggestions[0].confidence)  # → 0.7
```

---

## 🛠️ Future Implementation Plan

### Phase 1: Real Database Integration (Next Step)

```python
class ParameterMetadataService:
    def __init__(self, config):
        # Initialize database connections
        self.allen_brain_client = AllenBrainClient(
            api_key=config['allen_brain_api_key']
        )
        self.neuromorpho_client = NeuroMorphoClient()
        self.custom_db = connect_to_database(config['db_url'])
    
    def suggest_parameter_values(self, ...):
        suggestions = []
        
        # Query Allen Brain Atlas
        allen_results = self.allen_brain_client.query(
            parameter=parameter_name,
            species=species,
            region=context.get('brain_region')
        )
        for result in allen_results:
            suggestions.append(
                ParameterSuggestion(
                    value=result['mean_value'],
                    source="allen_brain",
                    confidence=result['sample_size'] / 1000,
                    description=result['description'],
                    species=result['species'],
                    citation=result['citation']
                )
            )
        
        # Query NeuroMorpho.org
        neuromorpho_results = self.neuromorpho_client.query(...)
        # ... add to suggestions ...
        
        # Rank by confidence and return top N
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:5]  # Top 5 suggestions
```

### Phase 2: Backend API Endpoint

```python
# Django view: gui/workflow_backend/django-project/app/metadata/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def suggest_parameters(request):
    parameter_name = request.GET.get('parameter_name')
    parameter_description = request.GET.get('description')
    species = request.GET.get('species', None)
    
    service = ParameterMetadataService(config=settings.METADATA_CONFIG)
    suggestions = service.suggest_parameter_values(
        parameter_name=parameter_name,
        parameter_description=parameter_description,
        species=species
    )
    
    return Response({
        'suggestions': [
            {
                'value': s.value,
                'source': s.source,
                'confidence': s.confidence,
                'description': s.description,
                'species': s.species,
                'citation': s.citation
            }
            for s in suggestions
        ]
    })

# URL: GET /api/metadata/parameters/suggest/?parameter_name=tau_m&description=membrane%20time%20constant&species=mouse
```

### Phase 3: Frontend Integration

```typescript
// gui/workflow_frontend/src/components/ParameterSuggestionModal.tsx

interface ParameterSuggestion {
  value: any;
  source: string;
  confidence: number;
  description: string;
  species?: string;
  citation?: string;
}

export const ParameterSuggestionModal: React.FC = ({ parameter, onSelect }) => {
  const [suggestions, setSuggestions] = useState<ParameterSuggestion[]>([]);
  
  useEffect(() => {
    // Fetch suggestions from backend
    fetch(`/api/metadata/parameters/suggest/?` + 
          `parameter_name=${parameter.name}&` +
          `description=${parameter.description}&` +
          `species=${selectedSpecies}`)
      .then(res => res.json())
      .then(data => setSuggestions(data.suggestions));
  }, [parameter, selectedSpecies]);
  
  return (
    <Modal>
      <h2>Parameter Suggestions for {parameter.name}</h2>
      <div>
        {suggestions.map((suggestion, idx) => (
          <SuggestionCard 
            key={idx}
            suggestion={suggestion}
            onSelect={() => onSelect(suggestion.value)}
          />
        ))}
      </div>
    </Modal>
  );
};
```

---

## 📚 Data Sources

### Planned External Sources

| Source | Type | What It Provides | Status |
|--------|------|-----------------|--------|
| **Allen Brain Atlas** | API | Cell types, electrophysiology, morphology | ⏳ To integrate |
| **NeuroMorpho.org** | API/DB | Neuron morphology, parameters | ⏳ To integrate |
| **NeuroML-DB** | Database | Standard NeuroML models | ⏳ To integrate |
| **PubMed/Literature** | Text Mining | Published parameter values | ⏳ Future |
| **Custom Databases** | User DB | Lab-specific data, experiments | ⏳ Framework ready |
| **ModelDB** | Repository | Published computational models | ⏳ Future |

### Custom Data Integration

Users can register their own data sources:

```python
# Register a custom source
def my_lab_database_query(parameter_name, description, species):
    # Query your lab's database
    results = query_lab_db(parameter_name, species)
    return [
        ParameterSuggestion(
            value=r['value'],
            source="my_lab",
            confidence=r['confidence'],
            description=r['description'],
            species=species,
            citation=r['paper']
        )
        for r in results
    ]

service = ParameterMetadataService()
service.register_custom_source("my_lab", my_lab_database_query)
```

---

## 🎯 Benefits

### For Researchers
- ⏱️ **Saves time**: No manual literature search
- 🎯 **Increases accuracy**: Data-driven parameter selection
- 🧪 **Enables exploration**: Easy to compare species/conditions
- 📚 **Provides citations**: Traceability to original sources

### For the Platform
- 🤖 **Enables AI assistance**: Foundation for intelligent workflow building
- 🔄 **Promotes reproducibility**: Parameters documented with sources
- 🌍 **Community knowledge**: Aggregate knowledge from all users
- 📈 **Continuous improvement**: Learn from successful models

---

## 🔍 Advanced Features (Future)

### 1. Semantic Search with Embeddings

```python
# Instead of keyword matching, use AI embeddings
parameter_embedding = embed_text(parameter_description)
database_embeddings = load_all_parameter_embeddings()

# Find most similar parameters in database
similarities = cosine_similarity(parameter_embedding, database_embeddings)
top_matches = get_top_k(similarities, k=10)
```

### 2. Context-Aware Ranking

```python
# Consider full workflow context
suggestions = service.suggest_with_context(
    parameter_name="tau_m",
    workflow_context={
        "model_type": "point_neuron",
        "network_size": 10000,
        "simulation_time": 1000,  # ms
        "other_parameters": {"V_reset": -70, "V_th": -55}
    }
)
# → Suggests parameters that work well with other parameters
```

### 3. Parameter Scaling Across Species

```python
# Automatically scale parameters based on known relationships
mouse_params = {"tau_m": 10.0, "C_m": 100.0}
human_params = service.scale_parameters(
    source_species="mouse",
    target_species="human",
    parameters=mouse_params
)
# → {"tau_m": 15.2, "C_m": 198.5} (scaled based on known relationships)
```

### 4. Uncertainty Quantification

```python
# Return not just a value, but a distribution
suggestion = ParameterSuggestion(
    value=10.5,  # Mean
    confidence=0.85,
    metadata={
        "distribution": "normal",
        "std": 2.3,  # Standard deviation
        "min": 6.1,
        "max": 15.8,
        "percentiles": {
            "25": 8.9,
            "50": 10.5,
            "75": 12.1
        }
    }
)
```

---

## 🎓 Summary

The **Parameter Suggestion Engine**:

1. **Solves a real problem**: Finding biological parameters is hard and time-consuming
2. **Uses multiple data sources**: Allen Brain Atlas, NeuroMorpho, custom databases, literature
3. **Provides structured suggestions**: Value, source, confidence, citation
4. **Supports species-specific queries**: Mouse, monkey, human, etc.
5. **Human-in-the-loop**: User reviews and selects suggestions
6. **Currently a stub**: Proof-of-concept with pattern matching
7. **Ready for integration**: Schema extended, service interface defined, tests passing
8. **Future work**: Real database connections, backend API, frontend UI, AI-powered ranking

### Current Status

✅ **Core infrastructure complete**  
✅ **Schema extended**  
✅ **Stub implementation working**  
✅ **Fully tested**  
⏳ **Real database integration next**  
⏳ **Backend/frontend UI pending**  

---

*For questions or to contribute, see the main documentation or create an issue on GitHub.*


