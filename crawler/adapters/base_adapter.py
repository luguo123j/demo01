"""Base adapter interface for multi-source novel crawling."""
from abc import ABC, abstractmethod
from typing import Dict, List


class BaseSourceAdapter(ABC):
    """Contract for source-specific crawler adapters."""

    def __init__(self, source_id: str, display_name: str, weight: int = 0):
        self.source_id = source_id
        self.display_name = display_name
        self.weight = weight

    @abstractmethod
    def search_novel(self, keyword: str) -> List[Dict[str, str]]:
        """Search novels by keyword."""

    @abstractmethod
    def get_novel_info(self, novel_url: str) -> Dict:
        """Get novel metadata and chapter list."""

    @abstractmethod
    def get_chapter_content(self, chapter_info: Dict) -> str:
        """Get chapter content by chapter reference."""

    @abstractmethod
    def close(self):
        """Release source resources."""
