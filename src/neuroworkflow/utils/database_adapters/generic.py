"""
Generic database adapter for user-configured custom databases.

This adapter can be configured dynamically to connect to various database APIs
using different patterns (REST API, GraphQL, etc.).
"""

import logging
import requests
import json
import statistics
from typing import Dict, List, Any, Optional
from .base import DatabaseAdapter
from ..parameter_metadata_service import ParameterSuggestion

logger = logging.getLogger(__name__)

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class GenericDatabaseAdapter(DatabaseAdapter):
    """
    Generic adapter for user-configured custom databases.
    
    This adapter attempts to connect to custom databases using various patterns:
    - REST API (GET/POST requests)
    - GraphQL (if endpoint provided)
    - SDK-based (if Python package specified)
    
    Configuration:
        - base_url: Base URL for the API
        - api_key: API key if required
        - adapter_type: 'rest_api', 'graphql', 'sdk'
        - query_endpoint: Endpoint path for querying (default: '/query' or '/search')
        - auth_type: 'api_key', 'bearer', 'basic', 'none'
        - headers: Additional headers to include
        - query_params_template: Template for building query parameters
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Adapter type (rest_api, graphql, sdk)
        self.adapter_type = self.config.get('adapter_type', 'rest_api')
        
        # Query endpoint configuration
        self.query_endpoint = self.config.get('query_endpoint', '/query')
        if not self.query_endpoint.startswith('/'):
            self.query_endpoint = '/' + self.query_endpoint
        
        # Authentication configuration
        self.auth_type = self.config.get('auth_type', 'api_key')
        self.headers = self.config.get('headers', {})
        
        # Query parameter template
        self.query_params_template = self.config.get('query_params_template', {})
        
        # Timeout configuration
        self.timeout = self.config.get('timeout', 10)
        
        # Maximum results to return
        self.max_results = self.config.get('max_results', 50)
        
        if not REQUESTS_AVAILABLE:
            logger.warning("requests library not available. Install with: pip install requests")
    
    def get_source_name(self) -> str:
        """Return the name of this database source."""
        return self.config.get('source_name', 'custom_db')
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with authentication."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            **self.headers  # User-provided headers
        }
        
        # Add authentication headers
        if self.auth_type == 'api_key' and self.api_key:
            # Try common API key header patterns
            api_key_header = self.config.get('api_key_header', 'X-API-Key')
            headers[api_key_header] = self.api_key
        elif self.auth_type == 'bearer' and self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.auth_type == 'basic' and self.api_key:
            # Basic auth (api_key should be "username:password")
            import base64
            credentials = base64.b64encode(self.api_key.encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'
        
        return headers
    
    def _build_query_params(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build query parameters from template."""
        params = self.query_params_template.copy()
        
        # Replace placeholders
        params = {
            k: v.replace('{parameter_name}', parameter_name)
               .replace('{parameter_description}', parameter_description)
               .replace('{species}', species or '')
            if isinstance(v, str) else v
            for k, v in params.items()
        }
        
        # Add common parameters
        if 'q' not in params and 'query' not in params:
            params['q'] = parameter_name
        if species and 'species' not in params:
            params['species'] = species
        
        return params
    
    def _query_rest_api(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ParameterSuggestion]:
        """Query using REST API pattern."""
        if not REQUESTS_AVAILABLE:
            return []
        
        suggestions = []
        
        try:
            # Build URL
            url = f"{self.base_url.rstrip('/')}{self.query_endpoint}"
            
            # Build headers
            headers = self._build_headers()
            
            # Build query parameters
            params = self._build_query_params(parameter_name, parameter_description, species, context)
            
            # Try GET request first
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException:
                # If GET fails, try POST with params in body
                try:
                    response = requests.post(
                        url,
                        json=params,
                        headers=headers,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    data = response.json()
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Failed to query custom database {self.base_url}: {e}")
                    return []
            
            # Extract values from response
            # Try common response patterns
            values = []
            
            # Pattern 1: List of objects with 'value' field
            if isinstance(data, list):
                for item in data[:self.max_results]:
                    if isinstance(item, dict):
                        value = item.get('value') or item.get('data') or item.get('parameter_value')
                        if value is not None:
                            try:
                                values.append(float(value))
                            except (ValueError, TypeError):
                                pass
            
            # Pattern 2: Object with 'results' or 'data' array
            elif isinstance(data, dict):
                results = data.get('results') or data.get('data') or data.get('items') or []
                if isinstance(results, list):
                    for item in results[:self.max_results]:
                        if isinstance(item, dict):
                            value = item.get('value') or item.get('data') or item.get('parameter_value')
                            if value is not None:
                                try:
                                    values.append(float(value))
                                except (ValueError, TypeError):
                                    pass
                
                # Also check if data itself has a value
                if 'value' in data:
                    try:
                        values.append(float(data['value']))
                    except (ValueError, TypeError):
                        pass
            
            # Calculate statistics
            if values:
                valid_values = [v for v in values if isinstance(v, (int, float)) and not (isinstance(v, float) and (v != v or v == float('inf') or v == float('-inf')))]
                
                if valid_values:
                    mean_value = statistics.mean(valid_values)
                    median_value = statistics.median(valid_values)
                    
                    # Create suggestion with mean value
                    suggestions.append(ParameterSuggestion(
                        value=mean_value,
                        source=self.get_source_name(),
                        confidence=0.6,  # Lower confidence for generic adapter
                        description=f"Average value from {len(valid_values)} records in custom database",
                        species=species,
                        metadata={
                            'median': median_value,
                            'count': len(valid_values),
                            'min': min(valid_values),
                            'max': max(valid_values),
                            'source_url': self.base_url
                        }
                    ))
        
        except Exception as e:
            logger.error(f"Error querying generic database adapter: {e}", exc_info=True)
        
        return suggestions
    
    def query_parameter(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ParameterSuggestion]:
        """
        Query the custom database for parameter values.
        
        Args:
            parameter_name: Name of the parameter
            parameter_description: Description of the parameter
            species: Species filter (mouse, monkey, human, etc.)
            context: Additional context (brain region, cell type, etc.)
        
        Returns:
            List of parameter suggestions from this database
        """
        if not self.is_available():
            logger.debug(f"Generic database adapter {self.get_source_name()} not enabled")
            return []
        
        if not REQUESTS_AVAILABLE:
            logger.debug("requests library not available")
            return []
        
        # Route to appropriate query method based on adapter type
        if self.adapter_type == 'rest_api':
            return self._query_rest_api(parameter_name, parameter_description, species, context)
        elif self.adapter_type == 'graphql':
            # TODO: Implement GraphQL query pattern
            logger.warning("GraphQL adapter type not yet implemented")
            return []
        elif self.adapter_type == 'sdk':
            # TODO: Implement SDK-based query pattern
            logger.warning("SDK adapter type not yet implemented")
            return []
        else:
            logger.warning(f"Unknown adapter type: {self.adapter_type}")
            return []
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the database.
        
        Returns:
            Dictionary with 'success', 'message', and optional 'error' keys
        """
        if not REQUESTS_AVAILABLE:
            return {
                'success': False,
                'error': 'requests library not available',
                'message': 'Please install requests: pip install requests'
            }
        
        try:
            # Try a simple health check or test endpoint
            test_url = f"{self.base_url.rstrip('/')}/health"
            headers = self._build_headers()
            
            try:
                response = requests.get(test_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    return {
                        'success': True,
                        'message': 'Connection successful (health check passed)'
                    }
            except requests.exceptions.RequestException:
                pass
            
            # If health check fails, try the base URL
            try:
                response = requests.get(self.base_url, headers=headers, timeout=5)
                # Any response (even 404) means the server is reachable
                return {
                    'success': True,
                    'message': f'Connection successful (server responded with status {response.status_code})'
                }
            except requests.exceptions.ConnectionError as e:
                return {
                    'success': False,
                    'error': 'Connection failed',
                    'message': f'Could not connect to {self.base_url}: {str(e)}'
                }
            except requests.exceptions.Timeout:
                return {
                    'success': False,
                    'error': 'Connection timeout',
                    'message': f'Connection to {self.base_url} timed out'
                }
            except requests.exceptions.RequestException as e:
                return {
                    'success': False,
                    'error': 'Request failed',
                    'message': f'Request to {self.base_url} failed: {str(e)}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': 'Unexpected error',
                'message': f'Error testing connection: {str(e)}'
            }
