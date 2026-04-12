"""
Connection tester for custom database adapters.

This module provides functionality to test connections to custom databases
and determine which adapter pattern works best.
"""

import logging
from typing import Dict, List, Any, Optional
from .generic import GenericDatabaseAdapter

logger = logging.getLogger(__name__)


class DatabaseConnectionTester:
    """
    Tests connections to custom databases and determines the best adapter pattern.
    """
    
    def __init__(self, openai_client=None):
        """
        Initialize the connection tester.
        
        Args:
            openai_client: Optional OpenAI client for AI-powered query optimization
        """
        self.openai_client = openai_client
    
    def test_adapter_patterns(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Test different adapter patterns to see which one works.
        
        Args:
            base_url: Base URL of the database
            api_key: API key if required
            config: Additional configuration
        
        Returns:
            Dictionary with:
                - success: bool
                - working_pattern: str or None
                - test_results: List of test results for each pattern
                - error: str or None
                - message: str
        """
        config = config or {}
        test_results = []
        
        # Test patterns to try
        patterns = [
            {
                'adapter_type': 'rest_api',
                'query_endpoint': '/query',
                'auth_type': 'api_key' if api_key else 'none',
                'api_key_header': 'X-API-Key'
            },
            {
                'adapter_type': 'rest_api',
                'query_endpoint': '/search',
                'auth_type': 'api_key' if api_key else 'none',
                'api_key_header': 'X-API-Key'
            },
            {
                'adapter_type': 'rest_api',
                'query_endpoint': '/api/query',
                'auth_type': 'bearer' if api_key else 'none'
            },
            {
                'adapter_type': 'rest_api',
                'query_endpoint': '/api/search',
                'auth_type': 'bearer' if api_key else 'none'
            },
            {
                'adapter_type': 'rest_api',
                'query_endpoint': '/',
                'auth_type': 'api_key' if api_key else 'none',
                'api_key_header': 'Authorization'
            }
        ]
        
        working_pattern = None
        
        for pattern in patterns:
            # Create adapter with this pattern
            adapter_config = {
                'base_url': base_url,
                'api_key': api_key or '',
                'source_name': 'test',
                'enabled': True,
                'openai_client': self.openai_client,
                **pattern,
                **config  # User-provided config overrides defaults
            }
            
            adapter = GenericDatabaseAdapter(adapter_config)
            
            # Test connection
            test_result = adapter.test_connection()
            test_result['pattern'] = pattern
            test_results.append(test_result)
            
            if test_result.get('success'):
                working_pattern = pattern
                logger.info(f"Found working pattern: {pattern['adapter_type']} with endpoint {pattern['query_endpoint']}")
                break
        
        if working_pattern:
            return {
                'success': True,
                'working_pattern': working_pattern,
                'test_results': test_results,
                'message': f"Successfully connected using {working_pattern['adapter_type']} pattern"
            }
        else:
            # Collect error messages
            errors = [r.get('error', 'Unknown error') for r in test_results if not r.get('success')]
            unique_errors = list(set(errors))
            
            return {
                'success': False,
                'working_pattern': None,
                'test_results': test_results,
                'error': 'No working pattern found',
                'message': f"Could not connect using any tested pattern. Errors: {', '.join(unique_errors)}",
                'suggestions': self._generate_suggestions(test_results, base_url, api_key)
            }
    
    def _generate_suggestions(
        self,
        test_results: List[Dict[str, Any]],
        base_url: str,
        api_key: Optional[str]
    ) -> List[str]:
        """Generate helpful suggestions based on test results."""
        suggestions = []
        
        # Check for common issues
        connection_errors = [r for r in test_results if 'Connection' in r.get('error', '')]
        timeout_errors = [r for r in test_results if 'timeout' in r.get('error', '').lower()]
        auth_errors = [r for r in test_results if r.get('error') and ('401' in str(r.get('error')) or '403' in str(r.get('error')))]
        
        if connection_errors:
            suggestions.append("Could not reach the server. Please check:")
            suggestions.append(f"  - Is the URL correct? ({base_url})")
            suggestions.append("  - Is the server running and accessible?")
            suggestions.append("  - Are there firewall/network restrictions?")
        
        if timeout_errors:
            suggestions.append("Connection timed out. The server might be slow or unreachable.")
        
        if auth_errors:
            suggestions.append("Authentication failed. Please check:")
            suggestions.append("  - Is the API key correct?")
            suggestions.append("  - Does the API require authentication?")
            suggestions.append("  - What authentication method does the API use? (API key header, Bearer token, etc.)")
        
        if not suggestions:
            suggestions.append("Please verify:")
            suggestions.append("  - The API endpoint URL is correct")
            suggestions.append("  - The API is accessible from this network")
            suggestions.append("  - The API documentation for the correct endpoint and authentication method")
        
        return suggestions
