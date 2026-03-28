"""Source adapters for novel providers."""
from .base_adapter import BaseSourceAdapter
from .bqg353_adapter import BQG353SourceAdapter

__all__ = ['BaseSourceAdapter', 'BQG353SourceAdapter']
