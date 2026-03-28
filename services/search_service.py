"""Search service for novel search functionality"""
import logging
from .source_registry import SourceRegistry
from .search_orchestrator import SearchOrchestrator

logger = logging.getLogger(__name__)


def search_novel(keyword: str) -> dict:
    """
    Search for novels by keyword

    Args:
        keyword: Search keyword

    Returns:
        Dictionary with success status and results or error message

    Example:
        {
            'success': True,
            'novels': [
                {
                    'title': 'Novel Title',
                    'url': '/book/123',
                    'author': 'Author Name',
                    'description': 'Description text'
                }
            ]
        }
    """
    registry = None
    try:
        if not keyword or not keyword.strip():
            return {
                'success': False,
                'error': 'Please enter a novel name'
            }

        registry = SourceRegistry()
        orchestrator = SearchOrchestrator(registry)

        result = orchestrator.search(keyword.strip())
        return result

    except Exception as e:
        logger.error(f"Error searching novel: {e}")
        return {
            'success': False,
            'error': f'Error searching: {str(e)}'
        }
    finally:
        if registry:
            registry.close_all()
