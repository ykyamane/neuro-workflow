"""
Database adapters for querying neuroscience databases.

This module provides adapters for connecting to real neuroscience databases
like Allen Brain Atlas, NeuroMorpho.org, PubMed/NCBI, NeuroML-DB, etc.
"""

from .base import DatabaseAdapter
from .allen_brain import AllenBrainAdapter
from .neuromorpho import NeuroMorphoAdapter
from .pubmed import PubMedAdapter
from .neuroml_db import NeuroMLDBAdapter
from .generic import GenericDatabaseAdapter
from .local_rag import LocalRAGAdapter

__all__ = [
    'DatabaseAdapter',
    'AllenBrainAdapter',
    'NeuroMorphoAdapter',
    'PubMedAdapter',
    'NeuroMLDBAdapter',
    'GenericDatabaseAdapter',
    'LocalRAGAdapter',
]

