"""
NeuroML-DB adapter for parameter metadata service.

Uses NeuroML-DB REST API to query published NeuroML models for parameter values.
"""

import logging
import requests
import json
import urllib3
from typing import Dict, List, Any, Optional

# Suppress SSL warnings for NeuroML-DB (they may have certificate issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from .base import DatabaseAdapter
from ..parameter_metadata_service import ParameterSuggestion, MetadataSource

logger = logging.getLogger(__name__)

# Try to import requests (optional dependency)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class NeuroMLDBAdapter(DatabaseAdapter):
    """
    Adapter for NeuroML-DB REST API.

    Documentation: https://neuroml-db.org/api
    API: https://neuroml-db.org/api
    
    Free to use, no API key required.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not self.base_url:
            self.base_url = "https://neuroml-db.org/api"
        
        self.max_results = self.config.get('max_results', 10)  # Limit results for performance
        # OpenAI client is available from base class (passed via config)

    def get_source_name(self) -> str:
        return MetadataSource.NEUROML_DB.value

    def query_parameter(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ParameterSuggestion]:
        """
        Query NeuroML-DB for parameter values from published NeuroML models.

        Strategy:
        1. Search NeuroML-DB for models matching the parameter
        2. Fetch model details
        3. Extract parameter values from model definitions
        4. Return suggestions with model citations

        Args:
            parameter_name: Name of the parameter
            parameter_description: Description of the parameter
            species: Species filter (if models have species metadata)
            context: Additional context

        Returns:
            List of parameter suggestions from NeuroML models
        """
        if not self.is_available():
            logger.debug("NeuroML-DB adapter not enabled")
            return []

        if not REQUESTS_AVAILABLE:
            logger.debug("requests library not available")
            return []

        suggestions = []

        try:
            # Use LLM to optimize NeuroML-DB search query if available
            if self.openai_client:
                search_query = self._llm_optimize_neuroml_query(
                    parameter_name, parameter_description, species, context
                )
                if not search_query:
                    # Fallback to manual query building
                    search_query = self._build_manual_neuroml_query(
                        parameter_name, parameter_description
                    )
            else:
                # Fallback to manual query building
                search_query = self._build_manual_neuroml_query(
                    parameter_name, parameter_description
                )

            # Search NeuroML-DB for models
            models = self._search_models(search_query, max_results=self.max_results)
            
            if not models:
                logger.debug(f"No NeuroML-DB models found for query: {search_query}")
                return []

            logger.info(f"Found {len(models)} NeuroML-DB models for parameter: {parameter_name}")

            # Extract parameter values from models
            for model in models[:5]:  # Limit to top 5 models
                model_id = model.get('id') or model.get('model_id')
                if not model_id:
                    continue
                
                # Fetch model details
                model_details = self._fetch_model_details(model_id)
                if not model_details:
                    continue
                
                # Extract parameter values from model
                extracted_values = self._extract_parameter_from_model(
                    parameter_name, parameter_description, model_details, species
                )
                suggestions.extend(extracted_values)

            logger.info(f"Generated {len(suggestions)} suggestions from NeuroML-DB")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying NeuroML-DB API: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error processing NeuroML-DB data: {e}", exc_info=True)

        return suggestions

    def _search_models(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search NeuroML-DB for models.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of model dictionaries
        """
        try:
            params = {'q': query}
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                timeout=10,
                verify=False  # NeuroML-DB may have SSL certificate issues
            )
            response.raise_for_status()
            
            data = response.json()
            
            # NeuroML-DB returns a list directly
            if isinstance(data, list):
                return data[:max_results]
            elif isinstance(data, dict):
                # Could be paginated or wrapped
                if 'results' in data:
                    return data['results'][:max_results]
                elif 'models' in data:
                    return data['models'][:max_results]
                elif 'data' in data:
                    return data['data'][:max_results]
            
            return []

        except Exception as e:
            logger.error(f"Error searching NeuroML-DB: {e}", exc_info=True)
            return []

    def _fetch_model_details(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific model.

        Args:
            model_id: NeuroML-DB model ID

        Returns:
            Model details dictionary or None
        """
        try:
            # Try different endpoints for model details
            endpoints_to_try = [
                f"{self.base_url}/model?id={model_id}",
                f"{self.base_url}/model/{model_id}",
                f"{self.base_url}/models/{model_id}",
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    response = requests.get(
                        endpoint,
                        timeout=10,
                        verify=False  # NeuroML-DB may have SSL certificate issues
                    )
                    response.raise_for_status()
                    data = response.json()
                    if data:  # Non-empty response
                        logger.debug(f"Successfully fetched model details from {endpoint}")
                        return data
                except requests.exceptions.RequestException:
                    continue
            
            logger.debug(f"All endpoints failed for model {model_id}")
            return None

        except Exception as e:
            logger.debug(f"Error fetching model details for {model_id}: {e}")
            return None

    def _llm_optimize_neuroml_query(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Use LLM to optimize NeuroML-DB search query.
        
        LLM considers:
        - NeuroML model terminology and conventions
        - Parameter synonyms in NeuroML context
        - Best search terms for finding relevant models
        - NeuroML model structure and naming
        """
        if not self.openai_client:
            return None
        
        try:
            context_info = ""
            if species:
                context_info += f"Species: {species}\n"
            if context:
                if 'brain_region' in context:
                    context_info += f"Brain region: {context['brain_region']}\n"
                if 'cell_type' in context:
                    context_info += f"Cell type: {context['cell_type']}\n"
            
            prompt = f"""You are helping to build an optimal NeuroML-DB search query to find computational models that contain a specific neuroscience parameter.

Parameter Name: {parameter_name}
Parameter Description: {parameter_description}
{context_info}

Your task: Generate the best NeuroML-DB search query to find models that likely contain this parameter.

Consider:
1. **NeuroML terminology**: NeuroML models use specific naming conventions (e.g., "V_rest" for resting potential, "tau_m" for membrane time constant)
2. **Parameter synonyms**: Include common synonyms used in computational models
3. **Model types**: Consider which types of NeuroML models might contain this parameter (cell models, channel models, network models)
4. **Search strategy**: NeuroML-DB accepts space-separated search terms, so use relevant keywords

Return ONLY a JSON object:
{{
  "query": "<optimized NeuroML-DB search query (space-separated terms)>",
  "reason": "<brief explanation of query strategy>"
}}

The query should:
- Use NeuroML-specific terminology when appropriate
- Include synonyms and related terms
- Be optimized for finding models with this parameter
- Use space-separated terms (NeuroML-DB search format)"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at searching NeuroML-DB for computational neuroscience models. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content.strip())
            query = data.get("query")
            reason = data.get("reason", "")
            
            if query:
                logger.info(f"LLM optimized NeuroML-DB query for '{parameter_name}': {reason}")
                return query
                
        except Exception as e:
            logger.debug(f"LLM query optimization failed: {e}, using manual query")
        
        return None

    def _build_manual_neuroml_query(
        self,
        parameter_name: str,
        parameter_description: str
    ) -> str:
        """
        Build NeuroML-DB search query manually (fallback when LLM not available).
        """
        # Build search query - NeuroML-DB search is flexible
        # Try parameter name first, then add description terms
        search_terms = [parameter_name.replace('_', ' ')]  # Replace underscores with spaces
        if parameter_description:
            # Add key terms from description
            desc_terms = self._extract_key_terms(parameter_description)
            if desc_terms:
                search_terms.extend(desc_terms[:2])  # Add top 2 terms
        
        # NeuroML-DB accepts space-separated search terms
        return " ".join(search_terms)

    def _extract_key_terms(self, description: str) -> List[str]:
        """Extract key terms from parameter description for search."""
        import re
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'for', 'of', 'to', 'and', 'or', 'is', 'are', 'was', 'were'}
        words = re.findall(r'\b\w+\b', description.lower())
        return [w for w in words if w not in stop_words and len(w) > 3]

    def _extract_parameter_from_model(
        self,
        parameter_name: str,
        parameter_description: str,
        model_details: Dict[str, Any],
        species: Optional[str] = None
    ) -> List[ParameterSuggestion]:
        """
        Extract parameter values from NeuroML model definition.

        NeuroML models contain parameter definitions in various formats.
        We need to search through the model structure to find matching parameters.
        """
        suggestions = []

        try:
            # NeuroML models can have parameters in different places:
            # - Cell definitions (biophysical properties)
            # - Channel definitions (channel parameters)
            # - Network parameters
            # - Simulation parameters
            
            # Try to find parameter in model structure
            parameter_value = self._find_parameter_in_model(parameter_name, model_details)
            
            if parameter_value is not None:
                # Build citation from model metadata
                citation = self._build_citation(model_details)
                
                suggestions.append(ParameterSuggestion(
                    value=float(parameter_value),
                    source=MetadataSource.NEUROML_DB.value,
                    confidence=0.7,  # Good confidence for model parameters
                    description=f"Parameter value from NeuroML model: {model_details.get('name', 'Unknown model')}",
                    species=species or model_details.get('species'),
                    citation=citation,
                    metadata={
                        'model_id': model_details.get('id'),
                        'model_name': model_details.get('name')
                    }
                ))

        except Exception as e:
            logger.debug(f"Error extracting parameter from model: {e}")

        return suggestions

    def _find_parameter_in_model(
        self,
        parameter_name: str,
        model_details: Dict[str, Any]
    ) -> Optional[float]:
        """
        Recursively search model structure for parameter value.

        NeuroML models have nested structures, so we need to search recursively.
        """
        # Normalize parameter name for matching
        param_lower = parameter_name.lower()
        
        # Common NeuroML parameter locations
        search_paths = [
            ['cells', 'biophysicalProperties', 'membraneProperties'],
            ['cells', 'biophysicalProperties', 'intracellularProperties'],
            ['cells', 'morphology'],
            ['channels'],
            ['synapses'],
            ['parameters'],
            ['model', 'parameters'],
        ]
        
        # Try direct paths first
        for path in search_paths:
            value = self._get_nested_value(model_details, path + [param_lower])
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        
        # Try fuzzy matching in all numeric fields
        def search_recursive(obj, depth=0):
            if depth > 5:  # Limit recursion depth
                return None
            
            if isinstance(obj, dict):
                for key, val in obj.items():
                    # Check if key matches parameter name (fuzzy)
                    if self._fuzzy_match(key, parameter_name):
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            pass
                    # Recurse
                    result = search_recursive(val, depth + 1)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = search_recursive(item, depth + 1)
                    if result is not None:
                        return result
            
            return None
        
        return search_recursive(model_details)

    def _get_nested_value(self, obj: Dict, path: List[str]) -> Any:
        """Get value from nested dictionary using path."""
        current = obj
        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            if current is None:
                return None
        return current

    def _fuzzy_match(self, key: str, parameter_name: str) -> bool:
        """Simple fuzzy matching between key and parameter name."""
        key_lower = key.lower()
        param_lower = parameter_name.lower()
        
        # Exact match
        if param_lower in key_lower or key_lower in param_lower:
            return True
        
        # Check for common variations
        variations = {
            'firing_rate': ['rate', 'firing', 'frequency'],
            'membrane_potential': ['v_rest', 'vrest', 'resting_potential', 'vm'],
            'tau_m': ['tau', 'time_constant', 'membrane_time_constant'],
            'input_resistance': ['r_input', 'rin', 'resistance'],
        }
        
        for param, variants in variations.items():
            if param_lower == param:
                if any(v in key_lower for v in variants):
                    return True
        
        return False

    def _build_citation(self, model_details: Dict[str, Any]) -> str:
        """Build a citation string from model information."""
        citation_parts = []
        
        model_name = model_details.get('name') or model_details.get('title')
        if model_name:
            citation_parts.append(f'NeuroML Model: "{model_name}"')
        
        authors = model_details.get('authors') or model_details.get('author')
        if authors:
            if isinstance(authors, list):
                authors_str = ", ".join(authors[:3])
            else:
                authors_str = str(authors)
            citation_parts.append(f"Authors: {authors_str}")
        
        year = model_details.get('year') or model_details.get('publication_year')
        if year:
            citation_parts.append(f"({year})")
        
        model_id = model_details.get('id') or model_details.get('model_id')
        if model_id:
            citation_parts.append(f"NeuroML-DB ID: {model_id}")
        
        return ". ".join(citation_parts) if citation_parts else "NeuroML-DB model"

