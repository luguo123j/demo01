"""Search service for novel search functionality"""
import logging
from crawler.novel_crawler import NovelCrawler
from crawler.base_crawler import SearchNotFoundError

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
    try:
        if not keyword or not keyword.strip():
            return {
                'success': False,
                'error': 'Please enter a novel name'
            }

        # Initialize crawler
        crawler = NovelCrawler()

        # Search novels
        novels = crawler.search_novel(keyword.strip())

        # Close crawler
        crawler.close()

        return {
            'success': True,
            'novels': novels
        }

    except SearchNotFoundError as e:
        logger.warning(f"Search not found: {e}")
        return {
            'success': False,
            'error': f'No novels found for "{keyword}"'
        }

    except Exception as e:
        logger.error(f"Error searching novel: {e}")
        return {
            'success': False,
            'error': f'Error searching: {str(e)}'
        }
