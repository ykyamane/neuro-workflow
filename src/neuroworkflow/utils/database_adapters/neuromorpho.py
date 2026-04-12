"""
NeuroMorpho.org database adapter.

This adapter connects to the NeuroMorpho.org API to retrieve
real neuronal morphology and parameter data.

No API key required - free public API.
Documentation: http://neuromorpho.org/apiReference.html
"""

import logging
import json
import statistics
from typing import Dict, List, Any, Optional

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from .base import DatabaseAdapter
from ..parameter_metadata_service import ParameterSuggestion

logger = logging.getLogger(__name__)


class NeuroMorphoAdapter(DatabaseAdapter):
    """
    Adapter for NeuroMorpho.org API.
    
    Documentation: http://neuromorpho.org/apiReference.html
    API: http://neuromorpho.org/api/
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not self.base_url:
            self.base_url = "https://neuromorpho.org/api"
        
        if not REQUESTS_AVAILABLE:
            logger.warning("requests library not available. Install with: pip install requests")
    
    def get_source_name(self) -> str:
        return "neuromorpho"
    
    def query_parameter(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ParameterSuggestion]:
        """
        Query NeuroMorpho.org for parameter values using REST API.
        
        Args:
            parameter_name: Name of the parameter
            parameter_description: Description of the parameter
            species: Species filter (mouse, rat, human, etc.)
            context: Additional context (brain_region, cell_type, etc.)
        
        Returns:
            List of parameter suggestions from NeuroMorpho.org
        """
        if not self.is_available():
            logger.debug("NeuroMorpho adapter not enabled")
            return []
        
        if not REQUESTS_AVAILABLE:
            logger.debug("requests library not available")
            return []
        
        suggestions = []
        
        try:
            # Map parameter name to NeuroMorpho morphometry field (with AI mapping support)
            use_ai = self.openai_client is not None
            field_name = self._map_parameter_name(parameter_name, parameter_description, use_ai_mapping=use_ai)
            if not field_name:
                logger.debug(f"Parameter {parameter_name} not mappable to NeuroMorpho fields")
                return []
            
            # Build query parameters
            params = {}
            # Default to mouse if species not provided (most common in NeuroMorpho)
            query_species = species or 'mouse'
            # Map species names
            species_map = {
                'mouse': 'mouse',
                'rat': 'rat',
                'human': 'human',
                'monkey': 'monkey',
                'cat': 'cat'
            }
            mapped_species = species_map.get(query_species.lower(), query_species.lower())
            params['q'] = f"species:{mapped_species}"
            
            # Add context filters if provided
            if context:
                fq_list = []
                if 'brain_region' in context:
                    fq_list.append(f"brain_region:{context['brain_region']}")
                if 'cell_type' in context:
                    fq_list.append(f"cell_type:{context['cell_type']}")
                if fq_list:
                    params['fq'] = fq_list
            
            # Query neurons with performance-optimized limit
            # Each neuron requires a separate API call for morphometry, so we limit to 15 for speed
            # 15 neurons still gives good statistics (mean, median) while being fast
            all_neurons = []
            max_neurons = 15  # Optimized for performance: each requires separate API call
            page_num = 0
            
            while len(all_neurons) < max_neurons:
                params['page'] = page_num
                neuron_url = f"{self.base_url}/neuron/select"
                response = requests.get(neuron_url, params=params, timeout=10)
                
                if response.status_code != 200:
                    logger.warning(f"NeuroMorpho API returned status {response.status_code}")
                    break
                
                data = response.json()
                neurons_on_page = data.get('_embedded', {}).get('neuronResources', [])
                
                if not neurons_on_page:
                    break
                
                # Add neurons up to our limit
                remaining = max_neurons - len(all_neurons)
                all_neurons.extend(neurons_on_page[:remaining])
                
                # Check if there are more pages and we haven't reached our limit
                total_pages = data.get('page', {}).get('totalPages', 0)
                if page_num >= total_pages - 1 or len(all_neurons) >= max_neurons:
                    break
                
                page_num += 1
            
            neurons = all_neurons
            
            if not neurons:
                logger.debug(f"No neurons found for query: {params}")
                return []
            
            logger.info(f"Retrieved {len(neurons)} neurons from NeuroMorpho (optimized for performance)")
            
            # Get morphometry data for neurons
            # Each requires a separate API call, so we process all 50 (already limited above)
            values = []
            for neuron in neurons:
                neuron_name = neuron.get('neuron_name')
                if not neuron_name:
                    continue
                
                try:
                    morpho_url = f"{self.base_url}/morphometry/name/{neuron_name}"
                    morpho_response = requests.get(morpho_url, timeout=3)  # Shorter timeout for faster failure
                    
                    if morpho_response.status_code == 200:
                        morpho_data = morpho_response.json()
                        if field_name in morpho_data:
                            value = morpho_data[field_name]
                            if value is not None:
                                try:
                                    values.append(float(value))
                                except (ValueError, TypeError):
                                    pass
                except Exception as e:
                    logger.debug(f"Error fetching morphometry for {neuron_name}: {e}")
                    continue
            
            # Generate suggestions from collected values
            if values:
                mean_val = statistics.mean(values)
                median_val = statistics.median(values)
                std_val = statistics.stdev(values) if len(values) > 1 else 0
                
                suggestions.append(ParameterSuggestion(
                    value=mean_val,
                    source="neuromorpho",
                    confidence=0.8 if len(values) > 10 else 0.6,
                    description=f"Mean value from {len(values)} neurons in NeuroMorpho.org database",
                    species=species or "mouse",
                    citation="Ascoli, G.A. et al. (2007). 'NeuroMorpho.Org: A Central Resource for Neuronal Morphologies.' Journal of Neuroscience, 27(35):9247-9251."
                ))
                
                if len(values) > 5:
                    suggestions.append(ParameterSuggestion(
                        value=median_val,
                        source="neuromorpho",
                        confidence=0.75,
                        description=f"Median value from {len(values)} neurons (range: {min(values):.2f} to {max(values):.2f})",
                        species=species or "mouse",
                        citation="NeuroMorpho.org database"
                    ))
                
                logger.info(f"Generated {len(suggestions)} suggestions from {len(values)} values")
            else:
                logger.debug(f"No values found for parameter {parameter_name} in NeuroMorpho")
        
        except Exception as e:
            logger.error(f"Error querying NeuroMorpho: {e}", exc_info=True)
        
        return suggestions
    
    def _map_parameter_name(
        self, 
        parameter_name: str, 
        parameter_description: str = "",
        use_ai_mapping: bool = True
    ) -> Optional[str]:
        """
        Map NeuroWorkflow parameter names to NeuroMorpho morphometry field names.
        
        Uses a hybrid approach:
        1. Manual mapping (fast, reliable)
        2. AI semantic matching (if no manual match and use_ai_mapping=True)
        3. Fuzzy string matching (fallback)
        """
        param_lower = parameter_name.lower()
        
        # Step 1: Manual mapping (fast, reliable)
        mapping = {
            # Morphological parameters (actual field names from API)
            'soma_surface': 'surface',  # Total surface area
            'soma_volume': 'volume',  # Total volume
            'total_length': 'pathDistance',  # Total path length
            'total_volume': 'volume',
            'total_surface': 'surface',
            'number_branches': 'n_branch',
            'number_stems': 'n_stems',
            'number_bifurcations': 'n_bifs',
            'width': 'width',
            'height': 'height',
            'depth': 'depth',
            'diameter': 'diameter',
            'dendrite_diameter': 'diameter',  # Dendrite diameter uses diameter field
            'dendritic_diameter': 'diameter',
            'path_length': 'pathDistance',
            'euclidean_distance': 'eucDistance',
            'branch_order': 'branch_Order',
            'contraction': 'contraction',
            'fragmentation': 'fragmentation',
            'partition_asymmetry': 'partition_asymmetry',
            'fractal_dimension': 'fractal_Dim',
            # Note: NeuroMorpho focuses on morphology, not electrophysiology
            # For ephys parameters, we might need to look at literature metadata
        }
        
        manual_match = mapping.get(param_lower)
        if manual_match is not None:
            return manual_match
        
        # Step 2: If no manual match and AI enabled, try AI semantic matching
        if use_ai_mapping and parameter_description and self.openai_client:
            ai_match = self._ai_map_parameter(parameter_name, parameter_description)
            if ai_match:
                logger.info(f"AI mapped '{parameter_name}' to '{ai_match}'")
                return ai_match
        
        # Step 3: Fuzzy string matching (fallback)
        fuzzy_match = self._fuzzy_map_parameter(parameter_name)
        if fuzzy_match:
            logger.info(f"Fuzzy matched '{parameter_name}' to '{fuzzy_match}'")
            return fuzzy_match
        
        return None
    
    def _get_available_fields(self) -> List[str]:
        """Get list of available field names from NeuroMorpho."""
        # Known fields from NeuroMorpho API
        return ['surface', 'volume', 'n_stems', 'n_bifs', 'n_branch', 
                'width', 'height', 'depth', 'diameter', 'eucDistance', 
                'pathDistance', 'branch_Order', 'contraction', 'fragmentation',
                'partition_asymmetry', 'fractal_Dim']
    
    def _ai_map_parameter(self, parameter_name: str, parameter_description: str) -> Optional[str]:
        """Use AI to semantically match parameter to database fields."""
        if not self.openai_client:
            return None
        
        available_fields = self._get_available_fields()
        if not available_fields:
            return None
        
        # Use same AI mapping approach as Allen Brain Atlas
        prompt = f"""You are helping to map a neuroscience parameter to a database field.

Parameter Name: {parameter_name}
Parameter Description: {parameter_description}

Available Database Fields:
{json.dumps(available_fields, indent=2)}

Your task: Find the best matching database field for this parameter.

Return ONLY a JSON object:
{{
  "matched_field": "<field_name>" or null,
  "confidence": <0.0 to 1.0>
}}

If no good match exists, return null."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You map neuroscience parameters to database fields. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content.strip())
            matched_field = data.get("matched_field")
            confidence = data.get("confidence", 0.0)
            
            if matched_field and confidence >= 0.6:
                return matched_field
        except Exception as e:
            logger.debug(f"Error in AI mapping: {e}")
        
        return None
    
    def _fuzzy_map_parameter(self, parameter_name: str) -> Optional[str]:
        """Use fuzzy string matching to find similar field names."""
        available_fields = self._get_available_fields()
        if not available_fields:
            return None
        
        param_lower = parameter_name.lower()
        for field in available_fields:
            field_lower = field.lower()
            if param_lower in field_lower or field_lower in param_lower:
                if any(word in field_lower for word in param_lower.split('_')):
                    return field
        
        return None

