"""
Allen Brain Atlas database adapter.

This adapter connects to the Allen Brain Atlas API to retrieve
real parameter values for neuroscience models.

Uses allensdk Python library (no API key required).
Documentation: https://allensdk.readthedocs.io/
"""

import logging
import json
import statistics
from typing import Dict, List, Any, Optional
from .base import DatabaseAdapter
from ..parameter_metadata_service import ParameterSuggestion

logger = logging.getLogger(__name__)

# Try to import allensdk
try:
    from allensdk.core.cell_types_cache import CellTypesCache
    ALLENSDK_AVAILABLE = True
except ImportError:
    ALLENSDK_AVAILABLE = False
    CellTypesCache = None


class AllenBrainAdapter(DatabaseAdapter):
    """
    Adapter for Allen Brain Atlas API.
    
    Documentation: https://portal.brain-map.org/atlases
    API: https://api.brain-map.org/
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not self.base_url:
            self.base_url = "https://api.brain-map.org/api/v2"
        
        # Initialize allensdk cache if available
        self.cache = None
        if ALLENSDK_AVAILABLE:
            try:
                manifest_file = self.config.get('manifest_file', 'cell_types/manifest.json')
                self.cache = CellTypesCache(manifest_file=manifest_file)
                logger.info("Allen Brain Atlas SDK initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Allen Brain Atlas SDK: {e}")
                self.cache = None
        else:
            logger.debug("allensdk not installed. Install with: pip install allensdk")
    
    def get_source_name(self) -> str:
        return "allen_brain"
    
    def query_parameter(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ParameterSuggestion]:
        """
        Query Allen Brain Atlas for parameter values using allensdk.
        
        Args:
            parameter_name: Name of the parameter
            parameter_description: Description of the parameter
            species: Species filter (mouse, human, etc.)
            context: Additional context
        
        Returns:
            List of parameter suggestions from Allen Brain Atlas
        """
        if not self.is_available():
            logger.debug("Allen Brain Atlas adapter not enabled")
            return []
        
        if not self.cache:
            logger.debug("Allen Brain Atlas SDK not available")
            return []
        
        suggestions = []
        
        try:
            # Map parameter name to Allen Brain Atlas field (with description for smart mapping)
            # Enable AI mapping if OpenAI client is available
            use_ai = self.openai_client is not None
            field_name = self._map_parameter_name(parameter_name, parameter_description, use_ai_mapping=use_ai)
            
            # Special case: firing_rate variants are calculated from avg_isi, not directly mapped
            # Handle: firing_rate, firing_rate_resting, firing_rate_active, firing_rate_maximum, etc.
            param_lower = parameter_name.lower()
            is_calculated_field = (
                param_lower in ['firing_rate', 'spike_rate', 'rate'] or
                param_lower.startswith('firing_rate_') or
                param_lower.startswith('spike_rate_')
            )
            
            if not field_name and not is_calculated_field:
                logger.debug(f"Parameter {parameter_name} not mappable to Allen Brain Atlas fields")
                return []
            
            # Get all cells
            cells = self.cache.get_cells()
            logger.info(f"Retrieved {len(cells)} cells from Allen Brain Atlas")
            
            # Filter by species if provided
            if species:
                # Map species names (mouse -> Mus musculus, etc.)
                species_map = {
                    'mouse': 'Mus musculus',
                    'human': 'Homo sapiens',
                    'rat': 'Rattus norvegicus',
                    'monkey': 'Macaca mulatta'
                }
                allen_species = species_map.get(species.lower(), species)
                # Handle both dict and string species formats
                filtered_cells = []
                for c in cells:
                    cell_species = c.get('species')
                    if isinstance(cell_species, dict):
                        species_name = cell_species.get('name', '')
                    elif isinstance(cell_species, str):
                        species_name = cell_species
                    else:
                        species_name = ''
                    # Match species (case-insensitive)
                    if species_name.lower() == allen_species.lower() or species_name == allen_species:
                        filtered_cells.append(c)
                cells = filtered_cells
                logger.info(f"Filtered to {len(cells)} cells for species: {species}")
            
            # Process cells for comprehensive statistics
            # Use optimized limit: 300 cells gives good statistics while being fast
            # This is 1.5x more than original (200) and still fast
            max_cells = 300
            cells_to_process = cells[:max_cells] if len(cells) > max_cells else cells
            logger.info(f"Processing {len(cells_to_process)} cells (out of {len(cells)} total) for statistics")
            
            # Extract parameter values
            values = []
            
            # Get all ephys features at once (more efficient)
            # CRITICAL: Match ephys features to cells using specimen_id
            # cell['id'] matches ephys_feature['specimen_id']
            try:
                all_ephys_features = self.cache.get_ephys_features()
                logger.debug(f"Loaded {len(all_ephys_features)} ephys features")
                
                # Create mapping: specimen_id -> ephys_feature for fast lookup
                ephys_by_specimen_id = {}
                for feature in all_ephys_features:
                    specimen_id = feature.get('specimen_id')
                    if specimen_id:
                        ephys_by_specimen_id[specimen_id] = feature
                logger.debug(f"Created mapping for {len(ephys_by_specimen_id)} ephys features")
            except Exception as e:
                logger.warning(f"Error getting all ephys features: {e}")
                ephys_by_specimen_id = {}
            
            # Match cells to their ephys features
            matched_count = 0
            for cell in cells_to_process:
                cell_id = cell.get('id')  # cell['id'] is the specimen_id for ephys features
                if not cell_id:
                    continue
                
                feature = ephys_by_specimen_id.get(cell_id)
                if not feature:
                    continue
                
                matched_count += 1
                
                # Special handling for calculated fields (firing_rate from avg_isi)
                if is_calculated_field:
                    # Calculate firing rate from avg_isi (average inter-spike interval)
                    avg_isi = feature.get('avg_isi')
                    if avg_isi is not None:
                        try:
                            avg_isi_float = float(avg_isi)
                            # avg_isi is in milliseconds, convert to Hz
                            if avg_isi_float > 0:
                                firing_rate = 1000.0 / avg_isi_float  # Convert ms to Hz
                                # Filter out unrealistic values (too high or too low)
                                if 0.1 <= firing_rate <= 100:  # Reasonable range: 0.1-100 Hz
                                    values.append(firing_rate)
                        except (ValueError, TypeError, ZeroDivisionError) as e:
                            logger.debug(f"Error calculating firing rate from avg_isi {avg_isi}: {e}")
                            pass
                # Check for direct field match
                elif field_name and field_name in feature:
                    value = feature[field_name]
                    if value is not None:
                        try:
                            values.append(float(value))
                        except (ValueError, TypeError):
                            pass
            
            logger.info(f"Matched {matched_count} cells with ephys features, extracted {len(values)} values")
            
            # If no values found, try alternative field names
            if not values:
                alt_fields = self._get_alternative_fields(parameter_name)
                for alt_field in alt_fields:
                    for cell in cells:
                        ephys_features = cell.get('ephys_features', [])
                        for feature in ephys_features:
                            if alt_field in feature:
                                value = feature[alt_field]
                                if value is not None:
                                    values.append(float(value))
                                break
                        if values:
                            break
                    if values:
                        break
            
            # Generate suggestions from collected values
            if values:
                # Filter out any invalid values (ensure all are proper floats)
                valid_values = []
                for v in values:
                    try:
                        float_val = float(v)
                        if not (float('inf') == float_val or float('-inf') == float_val):
                            valid_values.append(float_val)
                    except (ValueError, TypeError):
                        continue
                
                if not valid_values:
                    logger.debug(f"No valid values found after filtering for parameter {parameter_name}")
                    return suggestions
                
                # Calculate statistics
                try:
                    mean_val = statistics.mean(valid_values)
                    median_val = statistics.median(valid_values)
                    std_val = statistics.stdev(valid_values) if len(valid_values) > 1 else 0
                except Exception as e:
                    logger.error(f"Error calculating statistics: {e}, values: {valid_values[:5]}")
                    return suggestions
                
                # Create suggestions
                suggestions.append(ParameterSuggestion(
                    value=mean_val,
                    source="allen_brain",
                    confidence=0.8 if len(valid_values) > 10 else 0.6,
                    description=f"Mean value from {len(valid_values)} cells in Allen Brain Atlas Cell Types Database",
                    species=species or "mouse",
                    citation="Allen Institute for Brain Science. (2015). 'Cell Types Database.' https://celltypes.brain-map.org/"
                ))
                
                if len(valid_values) > 5:
                    suggestions.append(ParameterSuggestion(
                        value=median_val,
                        source="allen_brain",
                        confidence=0.75,
                        description=f"Median value from {len(valid_values)} cells (range: {min(valid_values):.2f} to {max(valid_values):.2f})",
                        species=species or "mouse",
                        citation="Allen Institute for Brain Science. (2015). 'Cell Types Database.'"
                    ))
                
                logger.info(f"Generated {len(suggestions)} suggestions from {len(valid_values)} values")
            else:
                logger.debug(f"No values found for parameter {parameter_name} in Allen Brain Atlas")
        
        except Exception as e:
            logger.error(f"Error querying Allen Brain Atlas: {e}", exc_info=True)
        
        return suggestions
    
    def _map_parameter_name(
        self, 
        parameter_name: str, 
        parameter_description: str = "",
        use_ai_mapping: bool = True
    ) -> Optional[str]:
        """
        Map NeuroWorkflow parameter names to Allen Brain Atlas field names.
        
        Uses a hybrid approach:
        1. Manual mapping (fast, reliable)
        2. AI semantic matching (if no manual match and use_ai_mapping=True)
        3. Fuzzy string matching (fallback)
        
        Args:
            parameter_name: Name of the parameter
            parameter_description: Description of the parameter (for AI matching)
            use_ai_mapping: Whether to use AI if manual mapping fails
        """
        param_lower = parameter_name.lower()
        
        # Step 1: Manual mapping (fast, reliable)
        # Note: firing_rate variants (firing_rate_resting, firing_rate_active, etc.) are handled
        # as calculated fields in query_parameter, not here
        mapping = {
            # Firing rate is calculated from avg_isi (handled specially in query_parameter)
            # All firing_rate variants are treated the same way
            'firing_rate': None,  # Special case - calculated from avg_isi
            'spike_rate': None,  # Special case
            'rate': None,  # Special case
            
            # Direct field mappings (actual field names)
            'input_resistance': 'input_resistance_mohm',
            'r_input': 'input_resistance_mohm',
            'membrane_resistance': 'input_resistance_mohm',
            'rheobase': 'rheobase_sweep_number',
            'adaptation': 'adaptation',
            'avg_isi': 'avg_isi',  # Average inter-spike interval
            'isi': 'avg_isi',
            'latency': 'latency',
            'ri': 'ri',  # Rebound index
            'f_i_curve_slope': 'f_i_curve_slope',
            
            # Peak and trough voltages (various protocols)
            'peak_v_long_square': 'peak_v_long_square',
            'peak_v_short_square': 'peak_v_short_square',
            'fast_trough_v_long_square': 'fast_trough_v_long_square',
        }
        
        manual_match = mapping.get(param_lower)
        if manual_match is not None:  # Explicitly check for None (not just falsy)
            return manual_match
        
        # Step 2: If no manual match and AI enabled, try AI semantic matching
        if use_ai_mapping and parameter_description:
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
        """Get list of available field names from Allen Brain Atlas."""
        try:
            ephys_features = self.cache.get_ephys_features()
            if ephys_features and len(ephys_features) > 0:
                return list(ephys_features[0].keys())
        except Exception as e:
            logger.debug(f"Error getting available fields: {e}")
        return []
    
    def _ai_map_parameter(self, parameter_name: str, parameter_description: str) -> Optional[str]:
        """
        Use AI to semantically match parameter to database fields.
        
        This uses the OpenAI client if available to intelligently match
        parameter names/descriptions to actual database field names.
        
        Process:
        1. Get list of available database fields
        2. Use AI to find best match based on parameter name + description
        3. Return the matched field name
        
        This is exactly what you described:
        - We see the set of available parameters in the database
        - AI picks the one that matches/seems to match our parameter
        """
        # Get available fields from database
        available_fields = self._get_available_fields()
        if not available_fields:
            return None
        
        # If we have OpenAI client, use it for intelligent matching
        if self.openai_client:
            try:
                return self._openai_map_parameter(parameter_name, parameter_description, available_fields)
            except Exception as e:
                logger.debug(f"OpenAI mapping failed, using heuristic: {e}")
        
        # Fallback: Simple heuristic matching
        return self._heuristic_map_parameter(parameter_name, parameter_description, available_fields)
    
    def _openai_map_parameter(
        self, 
        parameter_name: str, 
        parameter_description: str, 
        available_fields: List[str]
    ) -> Optional[str]:
        """
        Use OpenAI to intelligently match parameter to database fields.
        
        This is the AI-powered automatic mapping you described!
        """
        prompt = f"""You are helping to map a neuroscience parameter to a database field.

Parameter Name: {parameter_name}
Parameter Description: {parameter_description}

Available Database Fields:
{json.dumps(available_fields, indent=2)}

Your task: Find the best matching database field for this parameter.

Consider:
- Semantic meaning (e.g., "firing rate" might match "avg_isi" if we calculate rate from ISI)
- Field names that describe similar concepts
- Abbreviations and synonyms

Return ONLY a JSON object with this structure:
{{
  "matched_field": "<field_name>" or null,
  "confidence": <0.0 to 1.0>,
  "reason": "<brief explanation>"
}}

If no good match exists, return null for matched_field."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that maps neuroscience parameters to database fields. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            
            matched_field = data.get("matched_field")
            confidence = data.get("confidence", 0.0)
            
            if matched_field and confidence >= 0.6:  # Only use if confident
                logger.info(f"AI mapped '{parameter_name}' to '{matched_field}' (confidence: {confidence:.2f})")
                return matched_field
            
        except Exception as e:
            logger.debug(f"Error in OpenAI mapping: {e}")
        
        return None
    
    def _heuristic_map_parameter(
        self, 
        parameter_name: str, 
        parameter_description: str, 
        available_fields: List[str]
    ) -> Optional[str]:
        """
        Simple heuristic matching (fallback when AI not available).
        """
        param_lower = parameter_name.lower()
        desc_lower = parameter_description.lower()
        
        # Look for keywords in description that might match field names
        keywords = param_lower.split('_') + [w for w in desc_lower.split() if len(w) > 3]
        
        best_match = None
        best_score = 0
        
        for field in available_fields:
            field_lower = field.lower()
            score = 0
            
            # Score based on keyword matches
            for keyword in keywords:
                if len(keyword) > 2 and keyword in field_lower:
                    score += 1
                if field_lower in keyword or keyword in field_lower:
                    score += 2
            
            if score > best_score:
                best_score = score
                best_match = field
        
        # Only return if we have a reasonable match
        if best_score >= 2:
            logger.debug(f"Heuristic matched '{parameter_name}' to '{best_match}' (score: {best_score})")
            return best_match
        
        return None
    
    def _fuzzy_map_parameter(self, parameter_name: str) -> Optional[str]:
        """
        Use fuzzy string matching to find similar field names.
        
        This is a simple fallback that looks for similar field names
        in the available database fields.
        """
        available_fields = self._get_available_fields()
        if not available_fields:
            return None
        
        param_lower = parameter_name.lower()
        
        # Simple substring matching
        for field in available_fields:
            field_lower = field.lower()
            # Check if parameter name is in field name or vice versa
            if param_lower in field_lower or field_lower in param_lower:
                # Additional checks for common patterns
                if any(word in field_lower for word in param_lower.split('_')):
                    return field
        
        return None
    
    def _get_alternative_fields(self, parameter_name: str) -> List[str]:
        """Get alternative field names to try if primary mapping fails."""
        alternatives = {
            'firing_rate': ['mean_firing_rate', 'avg_firing_rate'],
            'membrane_potential': ['resting_membrane_potential', 'v_resting'],
            'tau_m': ['membrane_time_constant', 'tau'],
        }
        return alternatives.get(parameter_name.lower(), [])

