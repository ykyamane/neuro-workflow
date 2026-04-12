"""
Base class for database adapters.

All database adapters should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from ..parameter_metadata_service import ParameterSuggestion


class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.
    
    Each adapter connects to a specific neuroscience database and provides
    a unified interface for querying parameter values.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the database adapter.
        
        Args:
            config: Configuration dictionary with API keys, endpoints, etc.
                   Note: Some adapters don't require API keys (they're free)
                   - openai_client: Optional OpenAI client for AI-powered mapping
        """
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.base_url = self.config.get('base_url', '')
        # Some adapters don't need API keys (they're free), so enabled by default
        self.enabled = self.config.get('enabled', True)
        # OpenAI client for AI-powered parameter mapping (optional)
        self.openai_client = self.config.get('openai_client')
    
    @abstractmethod
    def query_parameter(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ParameterSuggestion]:
        """
        Query the database for parameter values.
        
        Args:
            parameter_name: Name of the parameter
            parameter_description: Description of the parameter
            species: Species filter (mouse, monkey, human, etc.)
            context: Additional context (brain region, cell type, etc.)
        
        Returns:
            List of parameter suggestions from this database
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this database source."""
        pass
    
    def is_available(self) -> bool:
        """
        Check if the adapter is configured and available.
        
        Note: Some adapters don't require API keys, so this may
        just check if the adapter is enabled.
        """
        return self.enabled

