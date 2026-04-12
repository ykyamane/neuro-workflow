"""
PubMed/NCBI E-utilities adapter for parameter metadata service.

Uses NCBI E-utilities API to search PubMed for parameter values mentioned in research papers.
"""

import logging
import requests
import xml.etree.ElementTree as ET
import re
import json
from typing import Dict, List, Any, Optional
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


class PubMedAdapter(DatabaseAdapter):
    """
    Adapter for PubMed/NCBI E-utilities API.

    Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25497/
    API: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
    
    Free to use, optional API key for higher rate limits.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not self.base_url:
            self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
        # API key is optional but recommended for higher rate limits
        # Without key: 3 requests/second
        # With key: 10 requests/second (default), can request higher
        self.api_key = self.config.get('api_key', '')
        self.max_results = self.config.get('max_results', 30)  # Search up to 30 papers (optimized for performance)

    def get_source_name(self) -> str:
        return MetadataSource.PUBMED.value

    def query_parameter(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ParameterSuggestion]:
        """
        Query PubMed for parameter values mentioned in research papers.

        Strategy:
        1. Search PubMed for papers mentioning the parameter
        2. Fetch abstracts for top results
        3. Use AI (if available) to extract parameter values from text
        4. Return suggestions with paper citations

        Args:
            parameter_name: Name of the parameter
            parameter_description: Description of the parameter
            species: Species filter (mouse, human, etc.)
            context: Additional context

        Returns:
            List of parameter suggestions from PubMed papers
        """
        if not self.is_available():
            logger.debug("PubMed adapter not enabled")
            return []

        if not REQUESTS_AVAILABLE:
            logger.debug("requests library not available")
            return []

        suggestions = []

        try:
            # Build search query - use more flexible PubMed syntax
            # PubMed works better with quoted phrases and OR operators
            # IMPORTANT: Add neuroscience filter to avoid unrelated papers
            search_parts = []
            
            # Add neuroscience filter to narrow results
            neuroscience_terms = [
                'neuron', 'neuronal', 'neural', 'brain', 'cortex', 'hippocampus',
                'synapse', 'dendrite', 'axon', 'spike', 'electrophysiology'
            ]
            # Use parameter name/description to determine if we need neuroscience filter
            needs_neuro_filter = any(term in parameter_name.lower() or 
                                    term in parameter_description.lower() 
                                    for term in neuroscience_terms)
            
            if needs_neuro_filter:
                # Add neuroscience filter to avoid unrelated papers (e.g., "dendritic cells" in immunology)
                search_parts.append('(neuron OR neuronal OR neural OR brain OR neuroscience)')
            
            # Add parameter name (try both quoted and unquoted)
            if parameter_name:
                # Remove underscores and use space-separated terms
                param_clean = parameter_name.replace('_', ' ')
                # For neuroscience parameters, be more specific
                if 'dendrite' in param_clean.lower():
                    search_parts.append('(dendrite OR dendritic)')
                    if 'diameter' in param_clean.lower():
                        search_parts.append('(diameter OR size)')
                elif 'soma' in param_clean.lower():
                    search_parts.append('(soma OR "cell body" OR "cell soma")')
                else:
                    search_parts.append(f'"{param_clean}"')
            
            # Add description terms (use OR for synonyms)
            if parameter_description:
                desc_terms = self._extract_key_terms(parameter_description)
                if desc_terms:
                    # Use first 2-3 key terms
                    desc_query = " OR ".join([f'"{term}"' for term in desc_terms[:3]])
                    if desc_query:
                        search_parts.append(f"({desc_query})")
            
            # Add species
            if species:
                # PubMed prefers scientific names for species
                species_map = {
                    'mouse': 'mice OR "Mus musculus"',
                    'rat': 'rat OR "Rattus norvegicus"',
                    'human': 'human OR "Homo sapiens"',
                    'monkey': 'monkey OR "Macaca"'
                }
                species_query = species_map.get(species.lower(), species)
                search_parts.append(f"({species_query})")
            
            # Add context terms if provided
            if context:
                if 'brain_region' in context:
                    search_parts.append(f'"{context["brain_region"]}"')
                if 'cell_type' in context:
                    search_parts.append(f'"{context["cell_type"]}"')

            # Build PubMed search query - use parameter name as keyword/phrase search
            # Add neuroscience-specific filters to get relevant papers
            if search_parts:
                # Add neuroscience filter to ensure we get relevant papers
                search_parts.append("(neuron OR neuronal OR neuroscience OR brain OR neural)")
                query = " AND ".join(search_parts)
            else:
                # Fallback: use parameter name as keyword search with neuroscience filter
                param_clean = parameter_name.replace('_', ' ')
                query = f'("{param_clean}" OR {param_clean}) AND (neuron OR neuronal OR neuroscience OR brain OR neural)'
            
            # Search PubMed comprehensively - get up to max_results papers
            pmids = self._search_pubmed(query, max_results=self.max_results)
            
            if not pmids:
                logger.debug(f"No PubMed results found for query: {query}")
                return []

            logger.info(f"Found {len(pmids)} PubMed papers for parameter: {parameter_name}")

            # Fetch abstracts with performance-optimized limit
            # 5 abstracts is fast and still gives good results
            max_abstracts = 5
            abstracts = self._fetch_abstracts(pmids[:max_abstracts])  # Process up to 5 papers for fast results
            
            # Extract parameter values from abstracts
            # If OpenAI is available, use it to extract values intelligently
            if self.openai_client:
                extracted_values = self._extract_values_with_ai(
                    parameter_name, parameter_description, abstracts, species
                )
                suggestions.extend(extracted_values)
            else:
                # Fallback: simple regex extraction (less accurate)
                extracted_values = self._extract_values_simple(parameter_name, abstracts)
                suggestions.extend(extracted_values)

            logger.info(f"Generated {len(suggestions)} suggestions from PubMed")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying PubMed API: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error processing PubMed data: {e}", exc_info=True)

        return suggestions

    def _llm_optimize_pubmed_query(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Use LLM to optimize PubMed search query.
        
        LLM considers:
        - Parameter synonyms and related terms
        - Neuroscience terminology
        - Best way to find parameter values in abstracts
        - PubMed search syntax and best practices
        """
        if not self.openai_client:
            return None
        
        try:
            # Build context for LLM
            context_info = ""
            if species:
                species_map = {
                    'mouse': 'mice OR "Mus musculus"',
                    'rat': 'rat OR "Rattus norvegicus"',
                    'human': 'human OR "Homo sapiens"',
                    'monkey': 'monkey OR "Macaca"'
                }
                context_info += f"Species: {species_map.get(species.lower(), species)}\n"
            
            if context:
                if 'brain_region' in context:
                    context_info += f"Brain region: {context['brain_region']}\n"
                if 'cell_type' in context:
                    context_info += f"Cell type: {context['cell_type']}\n"
            
            prompt = f"""You are helping to build an optimal PubMed search query to find research papers that mention a specific neuroscience parameter.

Parameter Name: {parameter_name}
Parameter Description: {parameter_description}
{context_info}

Your task: Generate the best PubMed search query to find papers that likely contain this parameter value.

Consider:
1. **Synonyms and related terms**: Include common synonyms (e.g., "firing rate" → "spike rate", "neural activity")
2. **Neuroscience terminology**: Use proper neuroscience terms researchers would use
3. **Parameter variations**: Include different ways the parameter might be described
4. **Value mentions**: Think about how researchers typically mention parameter values in abstracts
5. **PubMed syntax**: Use proper PubMed search syntax with AND, OR, parentheses, quotes

Return ONLY a JSON object:
{{
  "query": "<optimized PubMed search query>",
  "reason": "<brief explanation of query strategy>"
}}

The query should:
- Be specific enough to find relevant papers
- Include neuroscience context (neuron, neuronal, neuroscience, brain, neural)
- Use proper PubMed syntax
- Be optimized for finding parameter values in abstracts"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at building PubMed search queries for neuroscience research. Return only valid JSON."
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
                logger.info(f"LLM optimized query for '{parameter_name}': {reason}")
                return query
                
        except Exception as e:
            logger.debug(f"LLM query optimization failed: {e}, using manual query")
        
        return None

    def _build_manual_pubmed_query(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build PubMed search query manually (fallback when LLM not available).
        """
        search_parts = []
        
        # Start with parameter name (clean it up)
        param_clean = parameter_name.replace('_', ' ')
        
        # For neuroscience parameters, be more specific
        if 'dendrite' in param_clean.lower():
            search_parts.append('(dendrite OR dendritic)')
            if 'diameter' in param_clean.lower():
                search_parts.append('(diameter OR size)')
        elif 'soma' in param_clean.lower():
            search_parts.append('(soma OR "cell body" OR "cell soma")')
        else:
            search_parts.append(f'"{param_clean}"')
        
        # Add description terms (use OR for synonyms)
        if parameter_description:
            desc_terms = self._extract_key_terms(parameter_description)
            if desc_terms:
                # Use first 2-3 key terms
                desc_query = " OR ".join([f'"{term}"' for term in desc_terms[:3]])
                if desc_query:
                    search_parts.append(f"({desc_query})")
        
        # Add species
        if species:
            # PubMed prefers scientific names for species
            species_map = {
                'mouse': 'mice OR "Mus musculus"',
                'rat': 'rat OR "Rattus norvegicus"',
                'human': 'human OR "Homo sapiens"',
                'monkey': 'monkey OR "Macaca"'
            }
            species_query = species_map.get(species.lower(), species)
            search_parts.append(f"({species_query})")
        
        # Add context terms if provided
        if context:
            if 'brain_region' in context:
                search_parts.append(f'"{context["brain_region"]}"')
            if 'cell_type' in context:
                search_parts.append(f'"{context["cell_type"]}"')

        # Build PubMed search query - use parameter name as keyword/phrase search
        # Add neuroscience-specific filters to get relevant papers
        if search_parts:
            # Add neuroscience filter to ensure we get relevant papers
            search_parts.append("(neuron OR neuronal OR neuroscience OR brain OR neural)")
            query = " AND ".join(search_parts)
        else:
            # Fallback: use parameter name as keyword search with neuroscience filter
            param_clean = parameter_name.replace('_', ' ')
            query = f'("{param_clean}" OR {param_clean}) AND (neuron OR neuronal OR neuroscience OR brain OR neural)'
        
        return query

    def _search_pubmed(self, query: str, max_results: int = 10) -> List[str]:
        """
        Search PubMed and return list of PMIDs.

        Args:
            query: PubMed search query
            max_results: Maximum number of results to return

        Returns:
            List of PubMed IDs (PMIDs)
        """
        try:
            params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'xml'
            }
            
            if self.api_key:
                params['api_key'] = self.api_key

            response = requests.get(
                f"{self.base_url}/esearch.fcgi",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            pmids = []
            for id_elem in root.findall('.//Id'):
                if id_elem.text:
                    pmids.append(id_elem.text)

            return pmids

        except Exception as e:
            logger.error(f"Error searching PubMed: {e}", exc_info=True)
            return []

    def _fetch_abstracts(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch abstracts for given PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of dicts with 'pmid', 'title', 'abstract', 'authors', 'year'
        """
        if not pmids:
            return []

        try:
            params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml',
                'rettype': 'abstract'
            }
            
            if self.api_key:
                params['api_key'] = self.api_key

            response = requests.get(
                f"{self.base_url}/efetch.fcgi",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            abstracts = []

            for article in root.findall('.//PubmedArticle'):
                pmid_elem = article.find('.//PMID')
                pmid = pmid_elem.text if pmid_elem is not None else None

                # Get title
                title_elem = article.find('.//ArticleTitle')
                title = title_elem.text if title_elem is not None else ""

                # Get abstract
                abstract_elem = article.find('.//AbstractText')
                abstract = abstract_elem.text if abstract_elem is not None else ""

                # Get authors
                authors = []
                for author in article.findall('.//Author'):
                    last_name = author.find('LastName')
                    first_name = author.find('ForeName')
                    if last_name is not None and first_name is not None:
                        authors.append(f"{last_name.text}, {first_name.text}")

                # Get publication year
                pub_date = article.find('.//PubDate/Year')
                year = pub_date.text if pub_date is not None else None

                if pmid and (title or abstract):
                    abstracts.append({
                        'pmid': pmid,
                        'title': title,
                        'abstract': abstract,
                        'authors': authors[:3],  # First 3 authors
                        'year': year
                    })

            return abstracts

        except Exception as e:
            logger.error(f"Error fetching abstracts: {e}", exc_info=True)
            return []

    def _extract_key_terms(self, description: str) -> List[str]:
        """Extract key terms from parameter description for search."""
        # Simple extraction - remove common words
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'for', 'of', 'to', 'and', 'or', 'is', 'are', 'was', 'were'}
        words = re.findall(r'\b\w+\b', description.lower())
        return [w for w in words if w not in stop_words and len(w) > 3]

    def _extract_values_with_ai(
        self,
        parameter_name: str,
        parameter_description: str,
        abstracts: List[Dict[str, Any]],
        species: Optional[str] = None
    ) -> List[ParameterSuggestion]:
        """
        Use AI to extract parameter values from PubMed abstracts.

        This is more accurate than simple regex extraction.
        """
        if not self.openai_client or not abstracts:
            return []

        try:
            # Prepare abstracts text for AI
            abstracts_text = ""
            for ab in abstracts:
                abstracts_text += f"PMID: {ab['pmid']}\n"
                abstracts_text += f"Title: {ab['title']}\n"
                abstracts_text += f"Abstract: {ab['abstract']}\n"
                if ab.get('year'):
                    abstracts_text += f"Year: {ab['year']}\n"
                abstracts_text += "\n---\n\n"

            prompt = f"""You are analyzing neuroscience research papers to extract parameter values.

Parameter Name: {parameter_name}
Parameter Description: {parameter_description}
Species: {species or 'not specified'}

Here are PubMed abstracts that may mention this parameter:

{abstracts_text}

Your task: Extract specific numerical values for "{parameter_name}" mentioned in these abstracts.

For each value you find:
1. Extract the exact numerical value
2. Note the units (if mentioned)
3. Identify which paper it came from (PMID)
4. Assess confidence (0.0-1.0) based on how clearly the value is stated

Return a JSON object with this structure:
{{
  "values": [
    {{
      "value": <numeric value>,
      "pmid": "<PMID>",
      "units": "<units if mentioned>",
      "confidence": <0.0-1.0>,
      "context": "<brief context from abstract>"
    }}
  ]
}}

Only include values that are clearly stated in the abstracts. If no clear values are found, return an empty array.
Return ONLY valid JSON, no other text."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use same model as main service
                messages=[
                    {
                        "role": "system",
                        "content": "You extract numerical parameter values from neuroscience research papers. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            
            # Find corresponding abstracts for citations
            abstracts_by_pmid = {ab['pmid']: ab for ab in abstracts}

            suggestions = []
            for item in data.get('values', []):
                value = item.get('value')
                pmid = item.get('pmid')
                confidence = float(item.get('confidence', 0.6))
                
                if value is not None and pmid:
                    abstract_info = abstracts_by_pmid.get(pmid, {})
                    
                    # Build citation
                    citation = self._build_citation(abstract_info, pmid)
                    
                    # Build description
                    units = item.get('units', '')
                    context = item.get('context', '')
                    description = f"Value extracted from PubMed paper"
                    if units:
                        description += f" ({units})"
                    if context:
                        description += f": {context}"

                    suggestions.append(ParameterSuggestion(
                        value=float(value),
                        source=MetadataSource.PUBMED.value,
                        confidence=confidence,
                        description=description,
                        species=species,
                        citation=citation,
                        metadata={'pmid': pmid, 'units': units}
                    ))

            return suggestions

        except Exception as e:
            logger.warning(f"AI extraction from PubMed failed: {e}")
            return []

    def _extract_values_simple(
        self,
        parameter_name: str,
        abstracts: List[Dict[str, Any]]
    ) -> List[ParameterSuggestion]:
        """
        Simple regex-based extraction (fallback when AI not available).

        Less accurate but works without OpenAI.
        """
        suggestions = []
        
        # Convert parameter name to natural language variations
        # e.g., "dendrite_diameter" -> ["dendrite diameter", "dendritic diameter", "dendrite_diameter"]
        param_variations = self._get_parameter_variations(parameter_name)
        
        # Pattern to find numbers (including decimals) near parameter variations
        # Look for patterns like: "dendrite diameter: 2.5 μm" or "dendrite diameter was 2.5"
        patterns = []
        for variation in param_variations:
                # Escape special regex chars but keep spaces
                escaped = re.escape(variation).replace(r'\ ', r'\s+')
                # Match number after parameter name (with optional units)
                # More flexible: allows for "dendrite diameter of X" or "X μm dendrite diameter"
                # Also match without units for parameters like firing_rate, membrane_potential
                pattern1 = re.compile(
                    rf'\b{escaped}\s*[:\-=]?\s*(?:was|is|of|about|approximately|ranging|from|between)?\s*(\d+\.?\d*)\s*(?:μm|nm|mm|cm|mV|ms|Hz|pA|MΩ|mOhm|μM|mM|V|A|Ω|M)?',
                    re.IGNORECASE
                )
                # Reverse pattern: "X μm dendrite diameter" or "X mV"
                pattern2 = re.compile(
                    rf'(\d+\.?\d*)\s*(?:μm|nm|mm|cm|mV|ms|Hz|pA|MΩ|mOhm|μM|mM|V|A|Ω|M)?\s+{escaped}',
                    re.IGNORECASE
                )
                # Pattern for "parameter: X" or "parameter = X" (no units)
                pattern3 = re.compile(
                    rf'\b{escaped}\s*[:\-=]\s*(\d+\.?\d*)',
                    re.IGNORECASE
                )
                patterns.append(pattern1)
                patterns.append(pattern2)
                patterns.append(pattern3)

        for ab in abstracts:
            text = f"{ab['title']} {ab['abstract']}"
            
            for pattern in patterns:
                matches = pattern.findall(text)
                
                for match in matches[:2]:  # Limit to first 2 matches per abstract
                    try:
                        value = float(match)
                        # Only add if value is reasonable (not too large/small for typical neuroscience parameters)
                        if 0.001 <= abs(value) <= 1000000:
                            citation = self._build_citation(ab, ab['pmid'])
                            
                            suggestions.append(ParameterSuggestion(
                                value=value,
                                source=MetadataSource.PUBMED.value,
                                confidence=0.5,  # Lower confidence for regex extraction
                                description=f"Value extracted from PubMed paper using pattern matching",
                                species=None,
                                citation=citation,
                                metadata={'pmid': ab['pmid']}
                            ))
                            break  # Found a value, move to next abstract
                    except ValueError:
                        continue
                
                if suggestions:  # If we found a suggestion, don't try other patterns
                    break

        return suggestions

    def _get_parameter_variations(self, parameter_name: str) -> List[str]:
        """Generate natural language variations of parameter name."""
        variations = []
        
        # Original with underscores
        variations.append(parameter_name)
        
        # Replace underscores with spaces
        variations.append(parameter_name.replace('_', ' '))
        
        # Common neuroscience parameter variations
        param_map = {
            'dendrite_diameter': ['dendrite diameter', 'dendritic diameter', 'dendrite size'],
            'soma_volume': ['soma volume', 'cell body volume', 'soma size'],
            'firing_rate': ['firing rate', 'spike rate', 'firing frequency', 'spike frequency'],
            'membrane_potential': ['membrane potential', 'resting potential', 'V_rest', 'Vrest'],
            'tau_m': ['tau_m', 'tau membrane', 'membrane time constant', 'tau'],
            'input_resistance': ['input resistance', 'R_input', 'Rin', 'membrane resistance'],
        }
        
        # Add mapped variations if available
        if parameter_name.lower() in param_map:
            variations.extend(param_map[parameter_name.lower()])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for v in variations:
            v_lower = v.lower()
            if v_lower not in seen:
                seen.add(v_lower)
                unique_variations.append(v)
        
        return unique_variations

    def _build_citation(self, abstract_info: Dict[str, Any], pmid: str) -> str:
        """Build a citation string from abstract information."""
        authors = abstract_info.get('authors', [])
        year = abstract_info.get('year', '')
        title = abstract_info.get('title', '')
        
        citation_parts = []
        if authors:
            if len(authors) == 1:
                citation_parts.append(authors[0])
            elif len(authors) == 2:
                citation_parts.append(f"{authors[0]} & {authors[1]}")
            else:
                citation_parts.append(f"{authors[0]} et al.")
        
        if year:
            citation_parts.append(f"({year})")
        
        if title:
            citation_parts.append(f'"{title[:100]}..."')  # Truncate long titles
        
        citation_parts.append(f"PubMed PMID: {pmid}")
        
        return ". ".join(citation_parts) if citation_parts else f"PubMed PMID: {pmid}"

